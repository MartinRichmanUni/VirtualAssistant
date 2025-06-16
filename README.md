# Raspberry Pi Virtual Assistant

Created using Raspberry Pi 5 which uses a custom wake word to wake up and allow the user to speak and get replies. Big credit to Dev Miser [https://github.com/DevMiser/] with his DaVinci repository serving as the basis of this project

## Setting up the Raspberry Pi

If you have already setup or have working knowledge of the device, skip this step.

On startup, you will want to navigate to the relevant directory you want the project to be installed in (e.g. /home/username/Documents). Open up the terminal on the top left with the icon next to the folders icon.

With the terminal, type in the following command to navigate to chosen directory. For example, you could use:

```bash
cd Document
```

You will then want to clone the directory within your given folder with the following command:

```bash
git clone https://github.com/MartinRichmanUni/VirtualAssistant.git
```
## Setting up the Virtual Environment

To install all necessary packages, you will need to first create a virtual environment as to not change the system files on accident, as this can cause things to break.

Use the following command to initialise the virtual environment configuration folder, ensuring you are still within the chosen directory from before.

```bash
python -m venv env
```

After that, you can start the virtual environment with the command:

```bash
source env/bin/activate
```
Which should indicate it is active as it will show the following:
```bash
(env) $
```
To stop working within the virtual environment, either close the terminal or use the command:
```bash
deactivate
```
## Installing Packages and Dependencies
While in the virtual environment, run the following commands to install all necessary packages.
```bash
pip3 install --upgrade pip
sudo apt-get install portaudio19-dev [When asked if you want to continue, enter Y and press Enter]
pip3 install pyaudio
pip3 install pvrecorder
pip3 install pvporcupine
pip3 install pvcobra
pip3 install pvleopard
pip3 install --upgrade openai
pip3 install pygame
pip3 install colorama
pip3 install pillow
```
## Open the Python file
On the desktop, click the raspberry icon on the top left, navigate to Thonny with 'Programming > Thonny' and open it. Load the 'grok.py' file into the application.

## Getting necessary API keys
The software using the OpenAI API for the assistant and PicoVoice for the custom wake word. 

Navigate to [OpenAI](https://platform.openai.com/docs/overview) and create a new project. Once the project has been created, navigate to the dashboard at the top right of the screen, and then look for API Keys tab. Create a new secret key and copy and paste the generated key into the 'grok.py' file on the line 
```python
openai.api_key = "REPLACE_WITH_OPENAI_API_KEY"
```
Do the same for PicoVoice API by navigating to [PicoVoice](https://console.picovoice.ai/?referrer=docs) and generating a key. You will most likely need an account first but a free plan is available. Same as before, copy and paste into the 'grok.py' file on the line
```python
pv_access_key= "REPLACE_WITH_PICOVOICE_ACCESS_KEY"
```
## Creating a Custom Wake Word
The application allows for customisation in that different wake words can be used to initialise the assistant. By default, it is "Hey Grok", but this can be changed to suit your preference. Navigate to [PicoVoice](https://console.picovoice.ai/ppn) and follow the instructions to generate a .ppn file once successful. Ensure this file is saved into the same directory as the python script 'grok.py'. You will also need to change the keywords_path value on line 213. E.g.
```python
keyword_paths=['grok.ppn']
```
## Making Changes
The script allows for customisation, in that the system prompt and how the assistant acts, as well as timeout time can all be changed. 

On line 46, the String can be modified to your preference to change how the assistant acts. Though, don't forget to also update line 69 for any changes as this is what is resets to after the specified time.

The assistant's voice can also be modified by changing the value for key 'voice' on line 193. Various options are available with examples being provided on https://www.openai.fm/.
```python
voice="echo" 
```

Additionally, you can customise the timeout set on line 36, by changing it to a higher value, though don't go for anything too extreme.

## Running the Script

Ensure you are in the specified directory in which the 'grok.py' file is present in the terminal, and run the following command to startup the application. 

```bash
python3 grok.py
```
Once the application has successfully loaded, speak into the mic with the custom wake word (if using 'grok.ppn' it is "Hey Grok").

## Further Notes
Any adjustments to the code or addition of new features will be noted.
