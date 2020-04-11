# Assembly Helper

**Assembly Helper** is a simple script to build & run assembly programs in DOSBox. It may be helpful in the integration with some code editors, such as Visual Studio Code.

## How to use

### Preparation

1. Ensure you are working on Windows;
2. If you do not have any Python 3 distribution, install one;
3. Download and install [DOSBox](https://www.dosbox.com/). Find the location of `DOSBox.exe` (such as `C:\Program Files (x86)\DOSBox-7.4-3\DOSBox.exe`), which will be referred to as `<DOSBox.exe LOCATION>`;
4. Download the [assets](https://github.com/YangHanlin/asmhelper/releases/tag/v0.0) (either of the two archives);
5. Extract files from the archive. There will be a `DOSBoxWorkspace` folder and a `Autoexec.bat.txt` file;
6. Move the `DOSBoxWorkspace` folder to the location where you would like the workspace folder will reside. Remember its location, which will be referred to as `<DOSBOX WORKSPACE DIRECTORY>`;
7. Find and open the configuration file (try searching `DOSBox options`). Copy the content of `Autoexec.bat.txt` to **the `[autoexec]` section of the configuration file**.
8. Replace the `<DOSBOX WORKSPACE DIRECTORY>` with what it should really be.

### Download & Configure Assembly Helper

1. Clone (recommended because it enables you to stay updated) or download this repository;

2. Add the path to the local repository to the `PATH` environment variable;

3. Run `asmhelper.py --fix-config blabla`, you will see:

   ```
   asmhelper.py: info: Fixing configuration
   asmhelper.py: info: User configuration has been set to default
   ```

4. FInd `%USERPROFILE%\.config\asmhelper\config.json` and edit it to replace `<DOSBOX WORKSPACE DIRECTORY>` and `<DOSBox.exe LOCATION>` with what they should really be;

5. All done! Run `asmhelper.py (path to the assembly source file)` to take a glance. If you haven’t had a source file, [here is one](https://github.com/YangHanlin/asmhelper/releases/download/v0.0/misaka.asm). You will finally see this magical thing run in DOSBox, like the picture below:

   ![Result](https://i.loli.net/2020/04/11/hNuFVtmI1ZSvxXf.png)

### Further steps

- If you would like to configure VS Code tasks to use `asmhelper.py`, there is a [sample `tasks.json`](https://github.com/YangHanlin/asmhelper/releases/download/v0.0/tasks.json) for you to refer to.

## License

All contents in this repository, except as otherwise noted or belong to other copyright holder(s), are licensed under the [GNU General Public License 3.0 (GPLv3)](LICENSE).

The packed assets (`Assets.zip` or `Simplified-Assets.zip`) contain files extracted from a disk image with MS-DOS 6.22 and MASM 6.11 installed, both copyrighted properties of their respective copyright holders, including Microsoft Corporation.