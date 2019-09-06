from .forms import AddStudentForm, QueryStudentForm, QueryTeamForm, ChangeStudentNameForm, CalculateForm
from . import main
from ..models import Student, Team
from flask import flash, render_template, redirect, url_for, session
from .. import db
from datetime import datetime, timedelta
from sqlalchemy import or_


@main.route('/')
def index():
    teams = Team.query.all()
    partners = Student.query.filter_by(role='合伙人').all()
    return render_template('index.html', teams=teams, partners=partners)


@main.route('/add-student', methods=['GET', 'POST'])
def add_student():
    form = AddStudentForm()

    # 在没有任何数据的时候，添加第一个创始人
    if Student.query.count() == 0:
        team = Team(leader='创始人')
        student = Student(name='创始人',
                          role='团队领导',
                          referrer='创始人'
                          )
        student.team = team
        db.session.add(student)
        db.session.commit()
        flash('已经初始化了创始人.')

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
            flash('引荐人不存在！请输入正确的引荐人名字！')
            return redirect(url_for('main.add_student'))
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
        # 设置时间，在此时间内引荐足够的人数成为合伙人
        threemonthtime = student.timestamp - timedelta(hours=1)
        if referrer.name != '创始人' and \
                Student.query.filter(Student.referrer == referrer.name,
                                     Student.timestamp > threemonthtime).count() == 3:
            referrer.role = '合伙人'
            session['referrer_name'] = referrer.name
            db.session.add(referrer)
            db.session.commit()
            session['referrer_yes'] = True
        # 判断引荐人的引荐人是否提升为团队领导（leader）
        if referrer.name != '创始人' and \
                Student.query.filter_by(referrer=referrer_referrer.name, role='合伙人').count() == 2 and \
                referrer_referrer.role != '团队领导':
            referrer_referrer.role = '团队领导'
            session['referrer_referrer_name'] = referrer_referrer.name
            team = Team(leader=referrer_referrer.name)
            if team:
                flash('新增了一个团队.')
            db.session.add(team)

            # 定义递归调用，遍历某个team_leader_name领导的团队下的所有的成员，并将其团队更改为他的团队

            def traversal_members(team_leader_name):
                team_members = Student.query.filter_by(referrer=team_leader_name).all()
                for team_member in team_members:
                    team_member.team = team
                    db.session.add(team_member)
                    # flash('team changed...')
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
        return redirect(url_for('main.add_student'))
    return render_template('add-student.html',
                           form=form,
                           referrer_yes=session.get('referrer_yes'),
                           referrer_referrer_yes=session.get('referrer_referrer_yes'),
                           student_name=session.get('student_name'),
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
            flash('此学员不存在.')
            return redirect(url_for('main.query_student'))

        # 定义递归函数，计算一个在学员下的成员数量
        def calculate_member_count(student, member_count=0):
            query = Student.query.filter_by(referrer=student.name)
            students = query.all()
            if query.count() != 0:
                session['member_count'] = session['member_count'] + query.count()
                for student in students:
                    calculate_member_count(student, member_count=member_count)
        if student.name == '创始人':
            session['member_count'] = Student.query.count() - 1
        else:
            calculate_member_count(student)

        def find_partner(student):
            if student.role == '学员':
                user = student.referrer
                student = Student.query.filter_by(name=user).first()
                find_partner(student)
            elif student.role == '合伙人':
                return student.name
            else:
                return None
        student_partner = find_partner(student)
        return render_template('query-student.html', form=form, student=student, a=session.get('member_count'), student_partner=student_partner)
    return render_template('query-student.html', form=form)


@main.route('/query-team', methods=['GET', 'POST'])
def query_team():
    form = QueryTeamForm()
    if form.validate_on_submit():
        team = Team.query.filter_by(leader=form.leader.data).first()
        if team is None:
            flash('此团队不存在.')
            return redirect(url_for('main.index'))
        partners = Student.query.filter_by(team=team).filter_by(role='合伙人').all()
        students = Student.query.filter_by(team=team).all()
        partner_number = len(partners)
        student_number = len(students)
        # partner_number = Student.query.filter_by(team=team).filter_by(role='合伙人').count()
        # student_number = Student.query.filter_by(team=team).count()
        return render_template('query-team.html',
                               form=form,
                               team=team,
                               partners=partners,
                               students=students,
                               partner_number=partner_number,
                               student_number=student_number)
    return render_template('query-team.html', form=form)


@main.route('/team-info/<teamname>', methods=['GET', 'POST'])
def team_info(teamname):
    team = Team.query.filter_by(leader=teamname).first()
    if team is None:
        flash('此团队不存在.')
        return redirect(url_for('main.index'))
    students = Student.query.filter_by(team=team).all()
    partners = Student.query.filter_by(team=team).filter_by(role='合伙人').all()
    partner_number = len(partners)
    student_number = len(students)
    return render_template('team-info.html', partner_number=partner_number, student_number=student_number, teamname=teamname, partners=partners)


@main.route('/change-name/<name>', methods=['GET', 'POST'])
def change_name(name):
    form = ChangeStudentNameForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(name=name).first()
        if student is None:
            return redirect(url_for('main.index'))
        student.name = form.name.data
        db.session.add(student)
        if student.role == '团队领导':
            team = Team.query.filter_by(leader=name).first()
            team.leader = student.name
            db.session.add(team)
        students = Student.query.filter_by(referrer=name).all()
        for user in students:
            user.referrer = student.name
            db.session.add(user)
        db.session.commit()
        flash('修改成功！')
    form.name.data = name
    return render_template('change-name.html', form=form, name=name)


@main.route('/calculate', methods=['GET', 'POST'])
def calculate():
    form = CalculateForm()
    if form.validate_on_submit():
        session['partner_money'] = None
        session['leader_money'] = None
        student = Student.query.filter_by(name=form.name.data).first()
        partner = Student.query.filter_by(name=student.referrer, role='合伙人').first()
        leader = student.team.leader
        if partner is None:
            flash('此学员上级还没有合伙人')
            # return redirect(url_for('main.calculate'))
            session['leader_money'] = form.student_money.data * (form.leader_percent.data + form.partner_percent.data) * 0.01
        else:
            session['partner_money'] = form.student_money.data * form.partner_percent.data * 0.01
            session['leader_money'] = form.student_money.data * form.leader_percent.data * 0.01
        return render_template('calculate.html',
                               form=form,
                               partner=partner,
                               leader=leader,
                               partner_money=session.get('partner_money'),
                               leader_money=session['leader_money'])
    return render_template('calculate.html', form=form)

