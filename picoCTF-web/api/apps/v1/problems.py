"""Achievement related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource, reqparse, inputs
from api.common import PicoException
import api.problem
ns = Namespace('problems', description='Problem management')


@ns.route('/')
class ProblemList(Resource):
    "Get the full list of problems, or add a new problem."

    def get(self):
        return api.problem.get_all_problems()
