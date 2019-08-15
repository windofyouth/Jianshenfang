from .forms import AddStudentForm, QueryStudentForm, QueryTeamForm
from . import main
from ..models import Student, Team
from flask import flash, render_template, redirect, url_for, session
from .. import db
from sqlalchemy import or_


@main.route('/', methods=['GET', 'POST'])
def index():
    form = AddStudentForm()

    # 在没有任何数据的时候，添加第一个创始人
    if Student.query.count() == 0:
        team = Team(leader='wangshenhua')
        student = Student(name='wangshenhua',
                          role='leader',
                          referrer='wangshenhua'
                          )
        student.team = team
        db.session.add(student)
        db.session.commit()
        flash('you have inited the first partner.')

    # 删除所有人
    # if Team.query.count() != 0:
    #     teams = Team.query.all()
    #     for team in teams:
    #         db.session.delete(team)
    #     db.session.commit()
    #     flash('you have delete all teams.')
    # if Student.query.count() != 0:
    #     students = Student.query.all()
    #     for student in students:
    #         db.session.delete(student)
    #     db.session.commit()
    #     flash('you have delete all students.')

    if form.validate_on_submit():
        session['referrer_yes'] = False
        session['referrer_referrer_yes'] = False
        session['student_name'] = None
        session['referrer_name'] = None
        session['referrer_referrer_name'] = None
        referrer = Student.query.filter_by(name=form.referrer.data).first()
        referrer_referrer = Student.query.filter_by(name=referrer.referrer).first()
        # 判断引荐人是否存在，不存在报错返回到原始页面
        if referrer is None:
            flash('the referrer not exist! 引荐人不存在！请输入正确的引荐人名字！')
            return redirect(url_for('main.index'))
        # 考虑引荐人是自己的情况

        # 添加学员
        student = Student(name=form.name.data,
                          role=form.role.data,
                          referrer=form.referrer.data)
        session['student_name'] = student.name

        student.team = referrer.team
        db.session.add(student)
        db.session.commit()
        # 判断学员引荐人是否提升为合伙人（partner）
        if referrer.name != 'wangshenhua' and Student.query.filter_by(referrer=referrer.name).count() == 2:
            referrer.role = 'partner'
            session['referrer_name'] = referrer.name
            db.session.add(referrer)
            db.session.commit()
            session['referrer_yes'] = True
        # 判断引荐人的引荐人是否提升为团队领导（leader）
        if referrer.name != 'wangshenhua' and \
                Student.query.filter_by(referrer=referrer_referrer.name, role='partner').count() == 2 and \
                referrer_referrer.role != 'leader':
            referrer_referrer.role = 'leader'
            session['referrer_referrer_name'] = referrer_referrer.name
            team = Team(leader=referrer_referrer.name)
            if team:
                flash('team has been added.')
            db.session.add(team)

            # 定义递归调用，遍历某个team_leader_name领导的团队下的所有的成员，并将其团队更改为他的团队

            def traversal_members(team_leader_name):
                team_members = Student.query.filter_by(referrer=team_leader_name).all()
                for team_member in team_members:
                    team_member.team = team
                    db.session.add(team_member)
                    flash('team changed...')
                    member = Student.query.filter_by(referrer=team_member.name).count()
                    if member != 0:
                        traversal_members(team_member.name)

            traversal_members(referrer_referrer.name)
            db.session.add(referrer_referrer)
            db.session.commit()
            session['referrer_referrer_yes'] = True
        # 将相应参数传递给index.html模板，返回相应的反馈信息
        # return render_template('index.html', form=form, student=student, referrer=referrer,
        #                        referrer_referrer=referrer_referrer,
        #                        referrer_yes=referrer_yes,
        #                        referrer_referrer_yes=referrer_referrer_yes,
        #                        )
        return redirect(url_for('main.index'))
    return render_template('index.html',
                           form=form,
                           referrer_yes=session.get('referrer_yes'),
                           referrer_referrer_yes=session.get('referrer_referrer_yes'),
                           student_name = session.get('student_name'),
                           referrer_name=session.get('referrer_name'),
                           referrer_referrer_name=session.get('referrer_referrer_name')
                           )


@main.route('/query-student', methods=['GET', 'POST'])
def query_student():
    form = QueryStudentForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(name=form.name.data).first()
        session['member_count'] = 0
        if student is None:
            flash('The student not exist.')
            return redirect(url_for('main.query_student'))

        def calculate_member_count(student, member_count=0):
            query = Student.query.filter_by(referrer=student.name)
            students = query.all()
            if query.count() != 0:
                session['member_count'] = session['member_count'] + query.count()
                for student in students:
                    calculate_member_count(student, member_count=member_count)

        calculate_member_count(student)
        return render_template('query-student.html', form=form, student=student, a=session.get('member_count'))
    return render_template('query-student.html', form=form)


@main.route('/query-team', methods=['GET', 'POST'])
def query_team():
    form = QueryTeamForm()
    if form.validate_on_submit():
        team = Team.query.filter_by(leader=form.leader.data).first()
        if team is None:
            flash('The team not exist.')
        partner_number = Student.query.filter_by(team=team).filter_by(role='partner').count()
        # partner_number = team.students.query.filter_by(role='partner').count()
        student_number = Student.query.filter_by(team=team).count()
        return render_template('query-team.html', form=form, team=team, partner_number=partner_number, student_number=student_number)
    return render_template('query-team.html', form=form)
