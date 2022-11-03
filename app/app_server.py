#!/user/bin/python

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_bootstrap import Bootstrap5 as Bootstrap
import Genesys_Build_import as Genesys_Import
from Genesys_Build_import import pd, Genesys_Backend
from werkzeug.utils import secure_filename
import os
 
app = Flask(__name__)
Bootstrap(app)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    return render_template('base.html', title='Home Page')


@app.route("/prompt_creation", methods=['GET', 'POST'])
def prompt_import():
    Genesys_Backend.get_api_token()
    return render_template('prompt.html', title='Prompt Creation')

@app.route("/import")
def upload_page():
    Genesys_Backend.get_api_token()
    return render_template('upload.html', title='File Upload')

@app.route('/import/verify', methods=['GET','POST'])
def import_file():
    Genesys_Import.sync_backend()
    if request.method == "POST":
        file = request.files['file']
        f = file.filename
        file_ext = os.path.splitext(f)[1]
        if file and file_ext == '.xlsx':
            filename = secure_filename(f)
            file.save(os.path.join("files/", filename))
            build_excel = pd.read_excel(f"files/{f}",sheet_name=['Location','Queues','Schedules','Emergency Groups','Agents'],converters={'e164':str, 'Zip Code':str,'Caller ID Number':str,'Alerting Timeout':str,'Extension':str})
            convert_excel = Genesys_Import.import_excel(build_excel)
            global import_data 
            import_data = convert_excel['data']
        else:
            return  render_template("error.html")
            
    return render_template("importer.html",results=convert_excel['errors'],addressVerify=convert_excel['addressVerify'])

@app.route('/import/verify/build', methods=['GET','POST'])
def build_table():
    return render_template("table.html", locations=import_data['locations'],sites=import_data['sites'],
    queues=import_data['queues'],groups=import_data['groups'],schedules=import_data['schedules'],
    scheduleGroups=import_data['scheduleGroups'], emergencyGroups=import_data['emergencyGroups'],
    agents=import_data['agents'], callRoutes=import_data['callRoutes'])

@app.route('/import/template', methods=['GET','POST'])
def get_template():
    path = 'static/Genesys_Build_Template.xlsx'
    return send_file(path, as_attachment=True)

    
'''if __name__ == "__main__":
    app.run()'''