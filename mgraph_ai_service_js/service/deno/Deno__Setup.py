from os                                             import chmod
from pathlib                                        import Path
from osbot_utils.decorators.methods.cache_on_self   import cache_on_self
from osbot_utils.type_safe.Type_Safe                import Type_Safe
from osbot_utils.utils.Files                        import path_combine, current_temp_folder, create_folder, file_exists, file_not_exists
from osbot_utils.utils.Http                         import GET_bytes_to_file
from osbot_utils.utils.Process                      import exec_process
from osbot_utils.utils.Zip                          import unzip_file

FOLDER_NAME__DENO                    = 'deno-js'
FILE__NAME__DENO                     = 'deno'
#VERSION__DENO                        = 'v2.4.0'         # see https://github.com/denoland/deno/releases and https://docs.deno.com/runtime/fundamentals/stability_and_releases/
URL__GITHUB__DENO__RELEASES_DOWNLOAD = "https://github.com/denoland/deno/releases/download/"

class Deno__Setup(Type_Safe):

    def install(self) -> bool:                  # Download Deno if needed (32MB)  # todo: refactor to create a local install.json file which captures the status and stats of the download
        deno_path = self.file_path__deno()


        if file_exists(deno_path):
            return True

        import platform

        system  = platform.system().lower()
        machine = platform.machine().lower()


        if system == "linux":
            url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-x86_64-unknown-linux-gnu.zip"
        elif system == "darwin":
            if "arm" in machine:
                url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-aarch64-apple-darwin.zip"
            else:
                url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-x86_64-apple-darwin.zip"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")


        zip_path = self.file_path__deno_zip()
        if file_not_exists(zip_path):                                       # todo: see if there are significant performance benefits from doing this only in memory
            GET_bytes_to_file(url, zip_path)                                # download zip file
            unzip_file(zip_path, self.folder_path__deno_js())               # unzip it
            chmod(deno_path, 0o755)                                         # add execute privs
        return file_exists(deno_path)

    def setup(self):                            # Setup Deno and parser script
        self.folder_path__deno_js()             # ensure folder exists
        return self

    @cache_on_self
    def file_path__deno(self):
        return path_combine(self.folder_path__deno_js(), FILE__NAME__DENO)

    def file_path__deno_zip(self):
        return self.file_path__deno() + '.zip'

    @cache_on_self
    def folder_path__deno_js(self):
        deno_folder = path_combine(current_temp_folder(), FOLDER_NAME__DENO)
        create_folder(deno_folder)
        return deno_folder

    def execute(self, params):
        return exec_process(self.file_path__deno(), params)

    def eval(self, js_code, include_stderr = False):
        params = ["eval", js_code]
        result = exec_process(self.file_path__deno(), params)
        stderr = result.get('stderr')
        stdout = result.get('stdout').strip()
        if include_stderr:
            return stderr + stdout
        return stdout

    def run(self, js_code, include_stderr = False):
        params = ["run", js_code]
        result = exec_process(self.file_path__deno(), params)
        stderr = result.get('stderr')
        stdout = result.get('stdout').strip()
        if include_stderr:
            return stderr + stdout
        return stdout