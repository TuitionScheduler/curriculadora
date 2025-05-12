from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Table, MetaData

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Reflection setup
metadata = MetaData()
engine = create_engine('sqlite:///your-database.db')

# Reflect the 'courses' table
courses_table = Table('courses', metadata, autoload_with=engine)
grade_distributions_table = Table('grade_distributions', metadata, autoload_with=engine)
meetings_table = Table('meetings', metadata, autoload_with=engine)
programs_table = Table('programs', metadata, autoload_with=engine)
sections_table = Table('sections', metadata, autoload_with=engine)


# You can now query the 'courses' table without defining a model
@app.route('/course/<string:course_code>', methods=['GET'])
def get_course(course_code):
    course = db.session.query(courses_table).filter_by(course_code=course_code).first()
    course = dict(course)

    # If no course is found, return an error
    if not course:
        return jsonify('Course not found'), 404

    # Return the course as a dictionary
    return jsonify(course), 200

@app.route('/programs', methods=['GET'])
def get_programs():
    programs = db.session.query(programs_table).all()
    programs = dict(programs)

    # If no program is found, return an error
    if not programs:
        return jsonify('Programs not found'), 404

    # Return the programs as a dictionary
    return jsonify(programs), 200


# @app.route('//<string:>', methods=['GET'])
# def get_():
#      = db.session.query().filter_by(=).first()
#      = dict()

#     # If no  is found, return an error
#     if not :
#         return jsonify(' not found'), 404

if __name__ == '__main__':
    app.run(debug=True)














from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)  

class FetchModel:

    def __init__(self):
        self.conn = sqlite3.connect('your-database.db')
        self.conn.row_factory = sqlite3.Row  # This makes the rows act like dictionaries
        self.cursor = self.conn.cursor()

    def fetch_course(self, course_code):
        cursor = self.cursor
        query = ''' 
            SELECT course_code 
            FROM courses 
            WHERE course_code = ? 
        '''  
        cursor.execute(query, (course_code,))
        course = cursor.fetchone()
        self.conn.close()
        return course


class FetchController:

    def get_course(course_code):
        
        course_row = FetchModel.fetch_course(course_code)

        # Convert the query result to a list of dictionaries
        course = dict(course_row)  # Convert each Row into a dictionary

        # Return data as JSON
        return course  # Flask will convert the list of dictionaries to JSON



@app.route('/course/<string:course_code>', methods=['GET'])
def get_course(course_code):
    course = FetchController.get_course(course_code)
    return jsonify(course), 200

if __name__ == '__main__':
    app.run(debug=True)