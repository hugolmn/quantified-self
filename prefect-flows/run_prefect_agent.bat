@echo OFF
rem Adapted from: https://gist.github.com/maximlt/531419545b039fa33f8845e5bc92edd6
rem How to run a Prefect agent in a given conda environment from a batch file.

rem It doesn't require:
rem - conda to be in the PATH
rem - cmd.exe to be initialized with conda init

rem Define here the path to your conda installation
set CONDAPATH=C:\Users\HugoL\anaconda3
rem Define here the name of the environment
set ENVNAME=jupyterlab

rem The following command activates the base environment.
if %ENVNAME%==base (set ENVPATH=%CONDAPATH%) else (set ENVPATH=%CONDAPATH%\envs\%ENVNAME%)

rem Activate the conda environmentZ
rem Using call is required here, see: https://stackoverflow.com/questions/24678144/conda-environments-and-bat-files
call %CONDAPATH%\Scripts\activate.bat %ENVPATH%

rem Run a prefect agent in that environment
prefect agent start -q "quantified-self"

rem Deactivate the environment
call conda deactivate