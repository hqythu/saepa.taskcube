from flask import request
from flask import render_template
from flask import redirect
from flask import Markup
from . import main
from .forms import UserForm
from .. import db
from ..models import User
from .util import check
from .util import xmlparse
from .util import construct_text_message
from . import handler
from .exceptions import *


@main.route('/', methods=['GET'])
def hello_world():
    return 'Hello World!'


@main.route('/wechat', methods=['GET'])
def wechat_check():
    check_result = check.check_signature(
        request.args.get('signature', ''),
        request.args.get('timestamp', ''),
        request.args.get('nonce', ''),
        request.args.get('echostr', '')
    )
    if check_result:
        return request.args.get('echostr', '')
    else:
        return ''


@main.route('/wechat', methods=['POST'])
def wechat_response():
    message = xmlparse.get_message_by_xml(request.data)
    # TODO: 在Exception类内部处理回复信息而不是在这里使用多路的选择
    try:
        reply = construct_text_message(
            message,
            handler.handle(message)
        )
    except UserNotRegisteredException:
        reply = construct_text_message(
            message,
            Markup('你需要绑定账号：http://taskcube.hqythu.me/wechat/login/%s' %
                   message.get('FromUserName', ''))
        )
    except CommandNotFoundException:
        reply = construct_text_message(
            message,
            '不知道您在说什么'
        )
    except AlreadyDoTodayException:
        reply = construct_text_message(
            message,
            '您今天已经领取过该任务了'
        )
    except TimeNotMatchException:
        reply = construct_text_message(
            message,
            '现在这个时间不能领取该任务'
        )
    # except:
    #     reply = construct_text_message(
    #         message,
    #         '系统出了一点问题'
    #     )
    return render_template('reply_text.xml', msg=reply)


@main.route('/wechat/success', methods=['GET'])
def success():
    return render_template('success.html')


@main.route('/wechat/login/<openid>', methods=['GET', 'POST'])
def login(openid):
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            mobile=form.mobile.data,
            openid=openid,
            credits=0
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/wechat/success')
    return render_template('login.html', form=form)


@main.route('/wechat/share/<userid>', methods=['GET', 'POST'])
def share(userid):
    user = User.query.filter_by(username=userid).first()
    return render_template('share.html', user=user)
