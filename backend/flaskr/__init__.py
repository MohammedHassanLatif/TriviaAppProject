from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from typing import cast
from models import setup_db, Question, Category
from dotenv import load_dotenv

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS"
        )
        response.headers.add(
            "Access-Control-Allow-Origin", "*"
        )
        return response

    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        category = {category.id: category.type for category in categories}
        return jsonify({
            'success': True,
            "categories": category,
            "total_category": len(Category.query.all())
        })

    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        categories = Category.query.order_by(Category.id).all()
        all_categories = {
            category.id: category.type for category in categories}
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "categories": all_categories,
            "questions": current_questions,
            'total_questions': len(Question.query.all())
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_questions(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(400)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "deleted": question_id,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
            })

        except BaseException:
            abort(422)

    @app.route('/search', methods=['POST'])
    def search():
        body = request.get_json()
        search = body.get('searchTerm', None)

        selection = Question.query.order_by(
            Question.id).filter(
            Question.question.ilike(
                "%{}%".format(search)))
        current_questions = paginate_questions(request, selection)
        try:
            selection.first_or_404(1)
        except Exception as e:
            print(e)
            abort(404)
        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(selection.all())
        })

    @app.route('/questions/add', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(Question.query.all())
            })

        except BaseException:
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def retrieve_category_questions(category_id):
        try:
            selection = Question.query.order_by(
                Question.id).filter(
                Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)
            if not selection:
                abort(404)

            return jsonify({"success": True, "questions": current_questions, "total_questions": len(
                Question.query.filter(Question.category == category_id).all())})

        except Exception as e:
            print(e)
            abort(404)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        data = request.get_json()

        if 'searchTerm' not in data:
            abort(400)

        search_term = data['searchTerm']
        questions = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()
        formatted_questions = [question.format() for question in questions]

        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'total_questions': len(formatted_questions),
            'current_category': None
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        data = request.get_json()

        if 'previous_questions' not in data or 'quiz_category' not in data:
            abort(400)

        previous_questions = data['previous_questions']
        quiz_category = data['quiz_category']

        if quiz_category['id'] == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(
                category=quiz_category['id']).all()

        remaining_questions = [
            question for question in questions if question.id not in previous_questions]

        if len(remaining_questions) > 0:
            random_question = random.choice(remaining_questions).format()
        else:
            random_question = None

        return jsonify({
            'success': True,
            'question': random_question
        })

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': "Bad Request"
        }), 400

    @app.errorhandler(404)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': "resource not found"
        }), 404

    @app.errorhandler(405)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': "method not allowed"
        }), 405

    @app.errorhandler(422)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': "Unprocessable"
        }), 422

    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': "Internal Server Error"
        }), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run()
