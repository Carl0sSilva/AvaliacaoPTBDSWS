import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Disciplina(db.Model):
    __tablename__ = 'disciplinas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    alunos = db.relationship('Aluno', backref='disciplina', lazy='dynamic')

    def __repr__(self):
        return f'<Disciplina {self.name}>'


class Aluno(db.Model):
    __tablename__ = 'alunos'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    disciplina_id = db.Column(db.Integer, db.ForeignKey('disciplinas.id'))

    def __repr__(self):
        return f'<Aluno {self.username}>'

class NameForm(FlaskForm):
    name = StringField('Cadastre o novo aluno:', validators=[DataRequired()])
    disciplina = SelectField('Disciplina associada:', coerce=int)
    submit = SubmitField('Cadastrar')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Aluno=Aluno, Disciplina=Disciplina)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/alunos', methods=['GET', 'POST'])
def alunos():
    form = NameForm()
    form.disciplina.choices = [
        (disciplina.id, disciplina.name)
        for disciplina in Disciplina.query.order_by(Disciplina.name).all()
    ]

    if form.validate_on_submit():
        aluno = Aluno.query.filter_by(username=form.name.data).first()

        if aluno is None:
            aluno = Aluno(
                username=form.name.data,
                disciplina_id=form.disciplina.data
            )
            db.session.add(aluno)
            db.session.commit()
            session['known'] = False
            flash(f'Estudante cadastrado com sucesso!', 'success')
        else:
            session['known'] = True
            flash(f'Estudante já existe na base de dados!', 'warning')

        session['name'] = form.name.data
        return redirect(url_for('alunos'))

    alunos = Aluno.query.all()

    return render_template(
        'alunos.html',
        form=form,
        alunos=alunos,
        name=session.get('name'),
        known=session.get('known', False)
    )

@app.route('/')
def index():
    return render_template('index.html', current_time=datetime.now())

@app.route('/indisponivel')
def indisponivel():
    return render_template('indisponivel.html', current_time=datetime.now())
