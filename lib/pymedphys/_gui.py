# Copyright (C) 2019 Simon Biggs
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable = protected-access

import pathlib
import shutil

from pymedphys._imports import streamlit as st
from pymedphys._imports import tornado

HERE = pathlib.Path(__file__).parent.resolve()
STREAMLIT_CONTENT_DIR = HERE.joinpath("_streamlit")


def main(args):
    """Boot up the pymedphys GUI"""
    _fill_streamlit_credentials()

    streamlit_script_path = str(HERE.joinpath("_app.py"))

    if args.port:
        st.cli._apply_config_options_from_cli({"server.port": args.port})

    # Needs to run after config has been set
    _monkey_patch_streamlit_server()

    st._is_running_with_streamlit = True
    st.bootstrap.run(streamlit_script_path, "", [])


class HelloWorldHandler(  # pylint: disable = abstract-method
    tornado.web.RequestHandler
):
    def get(self):
        self.write("Hello world!")


def _monkey_patch_streamlit_server():
    """Adds custom URL routes to Streamlit's tornado server."""
    OfficialServer = st.server.server.Server
    official_create_app = OfficialServer._create_app

    def patched_create_app(self: st.server.server.Server) -> tornado.web.Application:
        app: tornado.web.Application = official_create_app(self)

        base: str = st.config.get_option("server.baseUrlPath")
        pattern = st.server.server_util.make_url_path_regex(base, "pymedphys")

        app.add_handlers(".*", [(pattern, HelloWorldHandler)])

        return app

    OfficialServer._create_app = patched_create_app


def _fill_streamlit_credentials():
    streamlit_config_file = pathlib.Path.home().joinpath(
        ".streamlit", "credentials.toml"
    )
    if streamlit_config_file.exists():
        return

    streamlit_config_dir = streamlit_config_file.parent
    streamlit_config_dir.mkdir(exist_ok=True)

    template_streamlit_config_file = STREAMLIT_CONTENT_DIR.joinpath("credentials.toml")

    try:
        shutil.copy2(template_streamlit_config_file, streamlit_config_file)
    except FileExistsError:
        pass
