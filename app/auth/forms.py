# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    otp_code = StringField('2FA Code (6 digits)', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Login')

class ResetOrRegisterForm(FlaskForm):
    secret_code = PasswordField('Invite / Master Secret Code', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Execute')