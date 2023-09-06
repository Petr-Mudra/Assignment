import re
from operator import itemgetter
from flask import Flask, request, render_template, json
from werkzeug.utils import secure_filename
from secret_key_generator import secret_key_generator
import os
import requests
from bs4 import BeautifulSoup
from random import randint

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key_generator.generate()
app.config["UPLOAD_FOLDER"] = 'src/static/upload_files'
app.config["NEW_FILE_FOLDER"] = 'src/static/new_files'
ALLOWED_EXTENSIONS = {'txt'}


def getTopOccuringWords(fileWithPath: str) -> dict:
    COUNTTOPRINT = 10

    try:
        file = open(file=fileWithPath, mode='r', encoding='utf-8')
        if file.readable():
            words = ((file.read()).strip('.,')).split(' ')
            file.close()
            wordCount = dict()

            for i in range(0, len(words)-1):
                w1 = (re.sub(pattern=r'([^\w]|_)+',
                             string=words[i], repl='')).lower()
                w2 = (re.sub(pattern=r'([^\w]|_)+',
                             string=words[i+1], repl='')).lower()
                if (((w1, w2) in wordCount) or ((w2, w1) in wordCount)):
                    if ((w1, w2) in wordCount):
                        wordCount[(w1, w2)] += 1
                    else:
                        wordCount[(w2, w1)] += 1
                else:
                    wordCount[(w1, w2)] = 1

            sWordCount = sorted(wordCount.items(), key=itemgetter(1),
                                reverse=True)
            topWordsTmp = sWordCount[0:COUNTTOPRINT]
            result = dict()
            {f'{sWordCount[0][0]}, {sWordCount[0][1]}': sWordCount[1]}
            while 0 != len(topWordsTmp):
                entry = topWordsTmp.pop(0)
                result[f'{entry[0][0]} {entry[0][1]}'] = entry[1]
            return result

        else:
            file.close()
            return str('File is not readable!')
    except FileNotFoundError as e:
        return str('Entered file was not found, please enter'
                   + f' a valid file and path!\n Error: {e}')


def articleToFile(articleName: str) -> str | bool:
    URL = 'https://en.wikipedia.org/wiki/'
    html = requests.get(f'{URL}{articleName}')
    bs = BeautifulSoup(html.text, 'lxml')
    title = bs.find('span', class_='mw-page-title-main')
    content = bs.find('div', id='mw-content-text')
    p = content.find_all('p')
    heading = content.find_all('span', class_='mw-headline')
    liTmp = content.find_all('li')

    li = list()
    for element in liTmp:
        if (element.find_parent('div', class_='navbox2')) is not None:
            continue
        elif (element.find_parent('div', class_='navbox noprint')) is not None:
            continue
        else:
            li.append(element)

    headingText = ''
    pText = ''
    liText = ''

    for h in heading:
        headingText = f'{headingText} {h.text}'
    for pa in p:
        pText = f'{pText} {pa.text}'
    for el in li:
        li = f'{li} {el.text}'
    fileName = f'{title.text}_{randint(0,9999999)}.txt'
    filePath = os.path.join(app.config['NEW_FILE_FOLDER'], fileName)
    file = open(filePath, 'w', encoding='utf-8')
    if file.writable():
        file.write(f'{headingText} \n {pText} \n {liText}')
        file.close()
        return fileName
    return False


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=['GET'])
def GET():
    if 'article' in request.args:
        fileName = articleToFile(request.args['article'])
        if fileName is not False:
            words = getTopOccuringWords(os.path.join(
                    app.config['NEW_FILE_FOLDER'], fileName))
            return (json.dumps(words, sort_keys=False))

    else:
        return render_template('makePost.html')


@app.route("/", methods=['POST'])
def POST():
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'No file selected!'
    file = request.files['file']
    fileName = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fileName))
    return (app.json.dumps(getTopOccuringWords(os.path.join(
        app.config['UPLOAD_FOLDER'], fileName)), sort_keys=False))


if __name__ == "__main__":
    app.run(host='localhost')
