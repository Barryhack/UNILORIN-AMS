from app.extensions import db
from datetime import datetime
import json

class SystemSettings(db.Model):
    """System settings model for managing application-wide configurations"""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20))  # string, int, float, bool, json
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # general, security, notification, etc.
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.String(10), db.ForeignKey('users.id'))
    updated_by_id = db.Column(db.String(10), db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<SystemSettings {self.key}>'

    def get_value(self):
        """Get the setting value with proper type conversion"""
        if not self.value:
            return None

        try:
            if self.value_type == 'int':
                return int(self.value)
            elif self.value_type == 'float':
                return float(self.value)
            elif self.value_type == 'bool':
                return self.value.lower() == 'true'
            elif self.value_type == 'json':
                return json.loads(self.value)
            else:  # string or unknown type
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.value

    def set_value(self, value, updated_by=None):
        """Set the setting value with proper type conversion"""
        if value is None:
            self.value = None
            self.value_type = 'string'
        elif isinstance(value, bool):
            self.value = str(value).lower()
            self.value_type = 'bool'
        elif isinstance(value, int):
            self.value = str(value)
            self.value_type = 'int'
        elif isinstance(value, float):
            self.value = str(value)
            self.value_type = 'float'
        elif isinstance(value, (dict, list)):
            self.value = json.dumps(value)
            self.value_type = 'json'
        else:
            self.value = str(value)
            self.value_type = 'string'

        if updated_by:
            self.updated_by_id = updated_by.id
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        return setting.get_value() if setting else default

    @classmethod
    def set_setting(cls, key, value, description=None, category='general', is_public=True, created_by=None):
        """Set a setting value, creating if it doesn't exist"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.set_value(value, updated_by=created_by)
            if description:
                setting.description = description
            if category:
                setting.category = category
            setting.is_public = is_public
        else:
            setting = cls(
                key=key,
                description=description,
                category=category,
                is_public=is_public,
                created_by_id=created_by.id if created_by else None
            )
            setting.set_value(value, updated_by=created_by)
            db.session.add(setting)
        db.session.commit()
        return setting

    @classmethod
    def get_all_settings(cls, include_private=False):
        """Get all settings, optionally including private ones"""
        query = cls.query
        if not include_private:
            query = query.filter_by(is_public=True)
        return query.all()

    @classmethod
    def get_settings_by_category(cls, category, include_private=False):
        """Get all settings in a category"""
        query = cls.query.filter_by(category=category)
        if not include_private:
            query = query.filter_by(is_public=True)
        return query.all()

    @classmethod
    def delete_setting(cls, key):
        """Delete a setting by key"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
            return True
        return False
