from pytest import mark
from src.utility.helper import infer_programming_language
from src.utility.filters import filter,Filter,FilterFactory,sorter_provider,sorter

@mark.parametrize("files",[("src/app.py","tests/report.txt","tests/test_dummy.py","tests/test_file_parser.py"),(".github/workflows/test-dev.yml",".github/workflows/testpypi_publish.yml",".gitignore","LICENSE","RAD.docx","README.md","main.py","pyproject.toml","requirements.txt","src/_internal/__init__.py","src/_internal/data_preprocessing.py","src/_internal/data_typing.py","src/_internal/file_parser.py","src/_internal/git_mining.py","src/_internal/info/ext.json","src/app/__init__.py","src/app/app.py","src/app/cli.py","src/gui/__init__.py","src/gui/components.py","src/gui/pages/homepage.py","src/utility/__init__.py","src/utility/logging_configs/logs_config_file.json","src/utility/logging_configs/logs_config_file_old.json","src/utility/logs.py","tests/test_cli.py","tests/test_data_preprocessing.py","tests/test_dummy.py","tests/test_file_parser.py","tests/test_git_miner.py")])
def test_infer_programming_language(files):
    assert infer_programming_language(files)==[".py"]

@mark.parametrize("numbers,comparison,expected",[
    ([1,5,2,6,3,8,34,6,3,7,3,789,3,5,3,55],33,3),
    ([1,5,2,6,3,8,34,6,3,7,3,789,3,5,3],33,2),
    ([1,5,2,6,3,8,6,3,7,3,3,5,3],33,0),
])
def test_filter_functions(numbers,comparison,expected):
    @filter("test_func")
    def test(value,comparison):
        return value > comparison
    fil:Filter = FilterFactory.create_filter("test_func")
    filtered=list(fil.run(numbers,comparison))
    assert len(filtered)==expected