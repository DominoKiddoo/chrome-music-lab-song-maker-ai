from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import ast

import time
import os
from openrouter import OpenRouter


with open("key.txt", "r", encoding="utf-8") as file:
    content = file.read()
apikey = content

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--log-level=3")

service = Service(log_output=os.devnull)


def askAi(prompt):
    with OpenRouter(api_key=apikey) as open_router:
        res = open_router.chat.send(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=False,
        )
        return(res.choices[0].message.content)


driver = webdriver.Chrome(service=service, options=options)
driver.get("https://musiclab.chromeexperiments.com/Song-Maker/")



input("press enter when your window is set up")

driver.execute_script("""
window.getCanvasesSorted = () => {
    const canvases = Array.from(document.querySelectorAll('canvas'));
    return canvases.sort((a, b) => (b.width * b.height) - (a.width * a.height));
};

window.toggleNote = (visibleCol, row) => {
    const canvases = window.getCanvasesSorted();
    if (!canvases.length) return;

    const visibleCols = 32;
    const isDrum = row >= 14;

    let targetCanvas, rect, areaTop, areaHeight, localRow, localTotalRows;

    if (isDrum) {
        localRow = row - 14; // Maps 14 -> 0 (snare), 15 -> 1 (kick)
        localTotalRows = 2;

        if (canvases.length > 1) {
            targetCanvas = canvases[1]; // 2nd largest canvas (percussion)
            rect = targetCanvas.getBoundingClientRect();
            areaTop = rect.top;
            areaHeight = rect.height;
        } else {
            targetCanvas = canvases[0]; // Main unified canvas
            rect = targetCanvas.getBoundingClientRect();
            areaTop = rect.top + (rect.height * 0.82);
            areaHeight = rect.height * 0.14;
        }
    } else {
        localRow = row; // Rows 0 to 13
        localTotalRows = 14;
        targetCanvas = canvases[0]; // Largest canvas (melody)
        rect = targetCanvas.getBoundingClientRect();
        areaTop = rect.top;
        areaHeight = canvases.length === 1 ? rect.height * 0.82 : rect.height;
    }

    const x = rect.left + ((visibleCol + 0.5) / visibleCols) * rect.width;
    const y = areaTop + ((localRow + 0.5) / localTotalRows) * areaHeight;

    const opts = {
        bubbles: true,
        cancelable: true,
        view: window,
        clientX: x,
        clientY: y,
        button: 0,
        buttons: 1
    };

    targetCanvas.dispatchEvent(new PointerEvent('pointerdown', opts));
    targetCanvas.dispatchEvent(new MouseEvent('mousedown', opts));
    targetCanvas.dispatchEvent(new PointerEvent('pointerup', opts));
    targetCanvas.dispatchEvent(new MouseEvent('mouseup', opts));
};

window.scrollGrid = (page) => {
    const canvases = window.getCanvasesSorted();
    if (!canvases.length) return;
    const canvas = canvases[0];
    const rect = canvas.getBoundingClientRect();

    const wheelOpts = {
        bubbles: true,
        cancelable: true,
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
        deltaX: rect.width,
        deltaY: 0,
        deltaMode: 0
    };
    canvas.dispatchEvent(new WheelEvent('wheel', wheelOpts));
    window.dispatchEvent(new WheelEvent('wheel', wheelOpts));

    const scrollThumb = document.querySelector('#scrollbar-container div, .scrollbar-thumb, [class*="scroll"]');
    if (scrollThumb) {
        const sRect = scrollThumb.getBoundingClientRect();
        const startX = sRect.left + sRect.width / 2;
        const startY = sRect.top + sRect.height / 2;
        const endX = rect.left + (page / 4) * rect.width + (sRect.width / 2);

        const downOpts = { bubbles: true, cancelable: true, view: window, clientX: startX, clientY: startY, button: 0, buttons: 1 };
        const moveOpts = { bubbles: true, cancelable: true, view: window, clientX: endX, clientY: startY, button: 0, buttons: 1 };
        const upOpts = { bubbles: true, cancelable: true, view: window, clientX: endX, clientY: startY, button: 0, buttons: 0 };

        scrollThumb.dispatchEvent(new PointerEvent('pointerdown', downOpts));
        scrollThumb.dispatchEvent(new MouseEvent('mousedown', downOpts));
        window.dispatchEvent(new PointerEvent('pointermove', moveOpts));
        window.dispatchEvent(new MouseEvent('mousemove', moveOpts));
        window.dispatchEvent(new PointerEvent('pointerup', upOpts));
        window.dispatchEvent(new MouseEvent('mouseup', upOpts));
    }
};

window.setInstrument = (instrument) => {
    const target = instrument;
    const btn = document.getElementById('instrument-toggle-button');

    for (let i = 0; i < 10; i++) {
    if (btn.textContent.trim().toLowerCase() === target.toLowerCase()) break;
    btn.click();
    }
};

window.setDrums = (drums) => {
    const target = drums;
    const btn = document.getElementById('percussion-toggle-button');

    for (let i = 0; i < 10; i++) {
    if (btn.textContent.trim().toLowerCase() === target.toLowerCase()) break;
    btn.click();
    }
};

window.setTempo = (tempo) => {
    const tempoInput = document.querySelector('input.input-number[name="tempo"]');
    tempoInput.value = tempo;
    tempoInput.dispatchEvent(new Event('input', { bubbles: true }));
    tempoInput.dispatchEvent(new Event('change', { bubbles: true }));
}
""")


def addNote(x,y):
    driver.execute_script(f"window.toggleNote({x},{y})")

print("registered functions")
idea = input("input prompt for the song: ")


def selectLen():
    while True:
        length = input("Type in how many bars long you want the song to be (1-16): ")
        try:
            length = int(length)
            if 1 <= length <= 16:
                return length
            else:
                print("Invalid length! (too high or low!)")
        except ValueError:
            print("length invalid!")

length = selectLen()


prompt = (
    """
    You are an AI with access to Chrome Music Lab Song Maker.
    Make a song out of the following prompt. Your response must be a plain 1D array 
    with no additional text or markdown formatting, formatted like this: ["Piano", "Electronic", 120, 0,0, 1,0, 2,2, 5,4]. 
    The first item is the instrument, it can either be "Piano", "Marimba", "Strings", "Woodwind" or "Synth"
    The second item is the drums. It can either be "Electronic", "Blocks", "Kit", or "Conga"
    the very thrid item is the TEMPO. It ranges from 40BPM to 240BPM. The rest are as follows
    Each pair of numbers is (column, row). 
    Columns represent time steps from left to right: there are 128 columns (0 to 127) (16 bars). 
    Rows represent musical pitch in a 2-octave C Major scale from top to bottom (14 rows, 0 to 13): 
    HOWEVER there are also rows 14 and 15 used for DRUMS. 14 is a snare, and 15 is a kick"
    Use chords (multiple notes in the same column) and rhythmic spacing to make it sound musical. 
    "Your prompt for the song is: "
    """ + idea + "ALSO, keep the song to be " + str(length) + " bars long"
)

print("generating")
response = ast.literal_eval(askAi(prompt))
print(response)

driver.execute_script("window.setInstrument(arguments[0])", response[0])
driver.execute_script("window.setDrums(arguments[0])", response[1])
driver.execute_script("window.setTempo(arguments[0])", response[2])


del response[0]
del response[0]
del response[0]

pairs = [(response[i], response[i+1]) for i in range(0, len(response), 2)]
pairs.sort(key=lambda x: x[0])


current_page = 0
for col, row in pairs:
    if col < 0 or col >= 128 or row < 0 or row >= 16:
        continue
    page = col // 32
    visible_col = col % 32

    if page != current_page:
        driver.execute_script(f"window.scrollGrid({page})")
        current_page = page
        time.sleep(0.3)

    addNote(visible_col, row)
    time.sleep(0.01)

time.sleep(3000)
