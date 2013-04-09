import datetime
import random
import quopri

from flask import Flask
from flask import abort
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from sqlobject import AND

from models import connect
from models import Domain
from models import Mail
from models import User
import settings

app = Flask(__name__)

@app.route("/")
def welcome():
	try:
		domains = list(Domain.select())
	except IndexError:
		domains = [settings.MY_DOMAINS[0],]
	about = settings.ABOUT
	return render_template('welcome.html', **locals())

@app.route("/redirect", methods=['GET', 'POST'])
def app_redirect():
	if request.method == 'POST':
		return redirect(url_for('list_mail', user=request.form['user'],
					domain=request.form.get('domain', settings.MY_DOMAINS[0])))
	else:
		if request.args.get('random', False):
			myrandom = "r"+('%030x' % random.randrange(256**15))[:15]
			return redirect(url_for('list_mail', user=myrandom, domain=settings.MY_DOMAINS[0]))
		abort(400)

@app.route("/<user>@<domain>/")
@app.route("/<user>/")
def list_mail(user, domain=settings.MY_DOMAINS[0]):
	try:
		mails = list(Mail.select(Mail.q.user==User.select(AND(User.q.name==user, Domain.q.name==domain))[0]))
	except IndexError:
		mails = []
	return render_template('list_mail.html', **locals())

@app.route("/<user>@<domain>/<int:mail_id>/")
@app.route("/<user>/<int:mail_id>/")
def show_mail(user, mail_id, domain=settings.MY_DOMAINS[0]):
	try:
		mail = list(Mail.select(AND(Mail.q.user==User.select(AND(User.q.name==user, Domain.q.name==domain))[0],
									Mail.q.id==mail_id)))[0]
	except IndexError:
		abort(404)
	new_mail = False
	if divmod((datetime.datetime.now() - mail.ts).total_seconds(), 60)[0] <= 10:
		new_mail = True
	mail_content = unicode(quopri.decodestring(mail.headers+"\r\n"+mail.body), 'utf-8', errors='ignore')
	return render_template('show_mail.html', **locals())

@app.route("/<user>@<domain>/<int:mail_id>/delete/")
@app.route("/<user>/<int:mail_id>/delete/")
def delete_mail(user, mail_id, domain=settings.MY_DOMAINS[0]):
	try:
		mail = list(Mail.select(AND(Mail.q.user==User.select(AND(User.q.name==user, Domain.q.name==domain))[0],
									Mail.q.id==mail_id)))[0]
	except IndexError:
		abort(404)
	if divmod((datetime.datetime.now() - mail.ts).total_seconds(), 60)[0] > 10:
		abort(403)
	Mail.delete(mail_id)
	return redirect(url_for('list_mail', user=user, domain=domain))

if __name__ == "__main__":
	connect()
	app.debug = settings.DEBUG
	app.run()
