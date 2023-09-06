import re
from operator import itemgetter
from flask import Flask, request, render_template, json
from flask_wtf import CSRFProtect
from werkzeug.utils import secure_filename
from secret_key_generator import secret_key_generator
import os
import requests
from bs4 import BeautifulSoup
from random import randint

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config["SECRET_KEY"] = secret_key_generator.generate()
app.config["UPLOAD_FOLDER"] = 'static/upload_files'
app.config["NEW_FILE_FOLDER"] = 'static/new_files'
ALLOWED_EXTENSIONS = {'txt'}


def getTopOccuringWords(fileWithPath: str) -> dict | str:
    """Reads file from parameter and returns its top 10 most occurring pairs
     of successive words. If file can not be opened or located, retruns string
     containing error message. File must be a .txt document.

    Args:
        fileWithPath (str): file name with a path

    Returns:
        dict: dictionary ordered by values, where key is two word pair string
        and value is its total count in text file
    """
    COUNTTOPRINT = 10
    try:
        file = open(file=fileWithPath, mode='r', encoding='utf-8')
        if file.readable():
            words = ((file.read()).strip('.,')).split(' ')
            file.close()
            wordCount = dict()

        # sanitize each word combination a store its count in dic (unordered)
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

            # sort dictionary by values, properly format structure in result
            # variable and return it
            sWordCount = sorted(wordCount.items(), key=itemgetter(1),
                                reverse=True)
            topWordsTmp = sWordCount[0:COUNTTOPRINT]
            result = dict()
            while 0 != len(topWordsTmp):
                entry = topWordsTmp.pop(0)
                result[f'{entry[0][0]} {entry[0][1]}'] = entry[1]
            return result

        else:
            file.close()
            return str('File is not readable!')
    except FileNotFoundError as e:
        return str('Entered file was not found, please enter'
                   + f' a valid file and path! \n Error: {e}')


def articleToFile(articleName: str) -> str | bool:
    """Fetcheds html from f'https://en.wikipedia.org/wiki/{articleName}' and
    stores its cleared text version in new file. File is created localy
     in app.config["NEW_FILE_FOLDER"]. If no errors occuress, returns created
     file name, otherwise returns False.

    Args:
        articleName (str): string specifing article to be stored to file,
        must return a valid page from URL:
        f'https://en.wikipedia.org/wiki/{articleName}'

    Returns:
        str | bool: False returned if any error occuress, string name of
        created file otherwise
    """
    URL = 'https://en.wikipedia.org/wiki/'
    html = requests.get(f'{URL}{articleName}')
    bs = BeautifulSoup(html.text, 'lxml')
    title = bs.find('span', class_='mw-page-title-main')
    content = bs.find('div', id='mw-content-text')
    p = content.find_all('p')
    heading = content.find_all('span', class_='mw-headline')
    liTmp = content.find_all('li')

    li = list()
    for element in liTmp:  # do not include element if it is from navigaton
        if (element.find_parent('div', class_='navbox2')) is not None:
            continue
        elif (element.find_parent('div', class_='navbox noprint')) is not None:
            continue
        else:
            li.append(element)

    # concate element lists into string
    headingText = ''
    pText = ''
    liText = ''
    for h in heading:
        headingText = f'{headingText} {h.text}'
    for pa in p:
        pText = f'{pText} {pa.text}'
    for el in li:
        li = f'{li} {el.text}'

    # create new file where name is "title_{intiger}", stores texts inside
    # and retruns file name
    fileName = f'{title.text}_{randint(0,9999999)}.txt'
    filePath = os.path.join(app.config['NEW_FILE_FOLDER'], fileName)
    file = open(filePath, 'w', encoding='utf-8')
    if file.writable():
        file.write(f'{headingText} \n {pText} \n {liText}')
        file.close()
        return fileName
    return False


def allowed_file(filename: str) -> bool:
    """Evaluates if file type is in ALLOWED_EXTENSIONS.

    Args:
        filename (str): name of file to be evaluated

    Returns:
        bool: True if file type is in ALLOWED_EXTENSIONS, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=['GET'])
def GET():
    """If paramether "article" specified, returns JSON including
    the top 10 most frequently occurring pairs of successive words
    in english wikipedia article from URL:
    'https://en.wikipedia.org/wiki/{articleName}'. If no article specified,
    returns basic page that enables ro send requests."
    """
    if 'article' in request.args and request.args['article'] != '':
        fileName = articleToFile(request.args['article'])
        if fileName is not False:
            words = getTopOccuringWords(os.path.join(
                    app.config['NEW_FILE_FOLDER'], fileName))
            return (json.dumps(words, sort_keys=False))

    return render_template('makePost.html')


@app.route("/", methods=['POST'])
def POST():
    '''If .txt file sent, calls getTopOccuringWords() on that file and
    result is returned as JSON. If file is not sent or has name eaqul to '',
    returns string "No file selected!".
    '''
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'No file selected!'
    file = request.files['file']
    fileName = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fileName))
    return (app.json.dumps(getTopOccuringWords(os.path.join(
        app.config['UPLOAD_FOLDER'], fileName)), sort_keys=False))


if __name__ == "__main__":
    app.run(host='localhost')
