"""
Jobs routes for Flask.

Blueprint routes for jobs endpoints.
"""

# Standard library
import asyncio
from typing import Optional

# Third-party
from flask import Blueprint, request, jsonify, g

# Local
from backend.app.modules.jobs.controllers import JobsController
from backend.app.modules.jobs.schemas import JobCreate, JobUpdate
from backend.app_flask.core.responses import success_response
from backend.app_flask.core.exceptions import NotFoundError, InternalError, ValidationError

# Create Blueprint
jobs_bp = Blueprint('jobs', __name__)

# Initialize controller
controller = JobsController()


def run_async(coro):
    """Run async function in Flask context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@jobs_bp.route('', methods=['GET'])
def list_jobs():
    """List all jobs, optionally filtered by account."""
    try:
        account_id = request.args.get('account_id', None)
        reload = request.args.get('reload', 'false').lower() == 'true'
        
        # Call async controller method
        result = run_async(controller.list_jobs(account_id=account_id, reload=reload))
        
        # Controller returns dict with success_response format
        return jsonify(result), 200
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve jobs: {str(e)}")


@jobs_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id: str):
    """Get job by ID."""
    try:
        result = run_async(controller.get_job(job_id))
        return jsonify(result), 200
    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve job: {str(e)}")


@jobs_bp.route('', methods=['POST'])
def create_job():
    """Create a new job."""
    try:
        job_data = request.get_json()
        if not job_data:
            raise ValidationError(message="Request body is required")
        
        # Convert dict to JobCreate schema
        # For Flask, we'll validate manually or use marshmallow
        # For now, pass dict and let controller handle validation
        job_create = JobCreate(**job_data)
        result = run_async(controller.create_job(job_create))
        return jsonify(result), 201
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to create job: {str(e)}")


@jobs_bp.route('/<job_id>', methods=['PUT'])
def update_job(job_id: str):
    """Update an existing job."""
    try:
        job_data = request.get_json()
        if not job_data:
            raise ValidationError(message="Request body is required")
        
        job_update = JobUpdate(**job_data)
        result = run_async(controller.update_job(job_id, job_update))
        return jsonify(result), 200
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to update job: {str(e)}")


@jobs_bp.route('/<job_id>', methods=['DELETE'])
def delete_job(job_id: str):
    """Delete a job."""
    try:
        result = run_async(controller.delete_job(job_id))
        return jsonify(result), 200
    except NotFoundError:
        raise
    except Exception as e:
        raise InternalError(message=f"Failed to delete job: {str(e)}")


@jobs_bp.route('/stats/summary', methods=['GET'])
def get_stats():
    """Get job statistics."""
    try:
        account_id = request.args.get('account_id', None)
        result = run_async(controller.get_stats(account_id=account_id))
        return jsonify(result), 200
    except Exception as e:
        raise InternalError(message=f"Failed to retrieve stats: {str(e)}")
