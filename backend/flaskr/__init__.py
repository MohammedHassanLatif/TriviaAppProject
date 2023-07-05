import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.sql.expression import func
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# paginate question (QUESTIONS_PER_PAGE questions per page)


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    formatted_questions = [question.format() for question in selection]
    return formatted_questions[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # CORS Headers

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # get all available categories

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories}
        return jsonify({
            'success': True,
            'categories': formatted_categories
        })

    # get paginated questions

    @app.route('/questions')
    def get_questions():

        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)
        # error 404. if there isn't any questions on the page
        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': formatted_categories,
            'current_category': None
        })

    # DELETE question using a question ID
    # When you click the trash icon next to a question

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            # error 404. if there isn't any question with question_id
            if question is None:
                abort(404)
            # delete
            question.delete()

            # renue query - get list of questions without deleted one
            # paginate questions
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            categories = Category.query.all()
            formatted_categories = {
                category.id: category.type for category in categories}

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(questions),
                'categories': formatted_categories,
                'current_category': None
            })
        except BaseException:
            abort(422)

    # POST a new question

    @app.route('/questions/add', methods=['POST'])
    def create_question():
        #body = request.get_json()
        # get data for new question
        new_question = request.json.get('question')
        new_answer = request.json.get('answer')
        new_difficulty = request.json.get('difficulty')
        new_category = request.json.get('category')
        if (new_question is None or new_answer is None
                or len(new_question) == 0 or len(new_answer) == 0):
            abort(422)
        try:
            # POST
            question = Question(
                question=new_question,
                answer=new_answer,
                difficulty=int(new_difficulty),
                category=new_category)
            question.insert()
            selection = Question.query.order_by('id').all()

            return jsonify({
                'success': True,
                'created': question.id,
                'total_questions': len(selection)
            })
        except BaseException:
            abort(404)

    # get questions based on a search term.
    # the search term is a substring of the question.

    @app.route('/questions', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm')

        if search_term is not None:
            # get relevant questions
            questions = Question.query.order_by(Question.id).filter(
                Question.question.ilike('%{}%'.format(search_term))).all()
            # paginate list of questions
            current_questions = paginate_questions(request, questions)

            categories = Category.query.all()
            formatted_categories = {
                category.id: category.type for category in categories}

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'categories': formatted_categories,
                'current_category': None
            })
        else:
            abort(400)

    # get questions based on category.
    # In the "List" tab / main screen, clicking on one of the
    # categories in the left column will cause only questions of that
    # category to be shown.

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):

        # if category don't exist
        if Category.query.get(category_id) is None:
            abort(404)

        # get questions
        questions = Question.query.order_by(
            Question.id).filter(
            Question.category == str(category_id)).all()

        current_questions = paginate_questions(request, questions)
        categories = Category.query.all()
        formatted_categories = {
            category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(questions),
            'categories': formatted_categories,
            'current_category': None
        })

    # get random questions to play the quiz.
    # reterned question is not one of the previous questions
    @app.route('/quizzes', methods=['POST'])
    def play_game():
        body = request.get_json()
        # take category and previous question parameters
        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')
        # get a random question
        try:
            if quiz_category['id'] == 0:
                # all categories
                current_question = Question.query.filter(
                    Question.id.notin_(previous_questions)).order_by(
                    func.random()).first().format()
            else:
                # given category
                current_question = Question.query.filter_by(
                    category=quiz_category['id']).filter(
                    Question.id.notin_(previous_questions)).order_by(
                    func.random()).first().format()

            return jsonify({
                'success': True,
                'question': current_question
            })
        except BaseException:
            abort(422)

    # error handlers for all expected errors

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Errort"
        }), 500
        
    @app.route('/')
    def hello():
        return 'Hello, World!'

    if __name__ == '__main__':
        app.run()

    return app