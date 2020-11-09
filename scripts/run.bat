set PATH=c:\python35\;c:\python35\scripts\;%PATH%
set FILE_FILTER=%1
set TESTS_FILTER="%2"

python -m pip install -r ../jobs_launcher/install/requirements.txt

python ..\jobs_launcher\executeTests.py --test_filter %TESTS_FILTER% --file_filter %FILE_FILTER% --tests_root ..\jobs --work_root ..\Work\Results --work_dir ML --cmd_variables ResPath "C:\TestResources\MLAssets" RMLTool "..\\RadeonML\\test_app.exe" WinMLTool "C:\ML\WinMLRunner\x64\WinMLRunner.exe" TensorRTTool "C:\ML\TensorRT-7.0.0.11\bin\trtexec.exe"