from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from app.models import User, db
from app.hardware.rfid_reader import RFIDReader
from app.hardware.fingerprint_sensor import FingerprintSensor
from app.decorators import admin_required
import json

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/admin/register-user', methods=['GET'])
@login_required
@admin_required
def register_user_form():
    """Display the user registration form"""
    return render_template('admin/register_user.html')

@registration_bp.route('/api/capture-rfid', methods=['POST'])
@login_required
@admin_required
def capture_rfid():
    """Endpoint to capture RFID tag data"""
    try:
        with RFIDReader() as reader:
            tag_id = reader.read_tag(timeout=30)
            if tag_id:
                # Check if RFID tag is already registered
                existing_user = User.query.filter_by(rfid_tag=tag_id).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'message': 'This RFID tag is already registered'
                    }), 400
                
                return jsonify({
                    'success': True,
                    'rfid_tag': tag_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No RFID tag detected'
                }), 400
    except Exception as e:
        current_app.logger.error(f"RFID capture error: {e}")
        return jsonify({
            'success': False,
            'message': 'Error capturing RFID tag'
        }), 500

@registration_bp.route('/api/capture-fingerprint', methods=['POST'])
@login_required
@admin_required
def capture_fingerprint():
    """Endpoint to capture fingerprint data"""
    try:
        with FingerprintSensor() as sensor:
            result = sensor.capture_fingerprint(timeout=30)
            if result:
                template_data, template_hash = result
                
                # Check if fingerprint is already registered
                existing_user = User.query.filter_by(fingerprint_hash=template_hash).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'message': 'This fingerprint is already registered'
                    }), 400
                
                return jsonify({
                    'success': True,
                    'template': template_data.hex(),  # Convert bytes to hex string for JSON
                    'template_hash': template_hash
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No fingerprint detected'
                }), 400
    except Exception as e:
        current_app.logger.error(f"Fingerprint capture error: {e}")
        return jsonify({
            'success': False,
            'message': 'Error capturing fingerprint'
        }), 500

@registration_bp.route('/api/register-user', methods=['POST'])
@login_required
@admin_required
def register_user():
    """Endpoint to register a new user with biometric data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'role', 
                         'matricNumber', 'rfidTag', 'fingerprintTemplate', 
                         'fingerprintHash']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check for existing user
        existing_user = User.query.filter(
            (User.email == data['email']) |
            (User.matric_number == data['matricNumber'])
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'User with this email or matric number already exists'
            }), 400
        
        # Create new user
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            role=data['role'],
            matric_number=data['matricNumber'],
            rfid_tag=data['rfidTag'],
            fingerprint_template=bytes.fromhex(data['fingerprintTemplate']),
            fingerprint_hash=data['fingerprintHash'],
            is_biometric_registered=True
        )
        
        # Generate a default password (can be changed later)
        default_password = f"{data['matricNumber']}@ams"
        new_user.set_password(default_password)
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'userId': new_user.id
        })
        
    except Exception as e:
        current_app.logger.error(f"User registration error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error registering user'
        }), 500
