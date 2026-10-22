# Discussion #46: Introducing Classroom 50

Source: https://github.com/foundation50/classroom50/discussions/46
Category: Announcements · Opened by @brianyu28 on 2026-07-01

> Verbatim capture of the thread. Comments are from the public; replies from
> maintainers (@rongxin-liu, @dmalan, @brianyu28) carry the most authority.

## Announcement (original post)

Today, we're releasing the first version of [Classroom 50](https://classroom50.org), a free and open-source tool for managing and grading programming assignments via GitHub. Supported by the [Fifty Foundation](https://fifty.foundation) as an open-source alternative to GitHub Classroom, Classroom 50 supports creating assignments, defining auto-graded correctness tests, and managing submissions.

Classroom 50 exists both as a web application (available at [https://classroom50.org](https://classroom50.org/)) and as a command-line tool. For information about getting started with Classroom 50, visit our [Wiki](https://github.com/foundation50/classroom50/wiki), where you'll find guides to both [the web interface](https://github.com/foundation50/classroom50/wiki/Web-Teacher-Guide) and [the CLI](https://github.com/foundation50/classroom50/wiki/Installation).

The Fifty Foundation will host two online training sessions to teach you how to use Classroom 50 and to answer your questions live. The sessions will take place at the following times:

- [Friday, July 24, 1pm-2pm EDT](https://time.cs50.io/20260724T1300-0400/PT1H?title=Classroom+50+Training+Session)
- [Friday, August 14, 1pm-2pm EDT](https://time.cs50.io/20260814T1300-0400/PT1H?title=Classroom+50+Training+Session)

To sign up to attend one of the training sessions, [complete the registration form here](https://docs.google.com/forms/d/e/1FAIpQLSdSZzOUOtSExmldFOsdlePWGZkJELHnZBpH3NPhXAJMDG9eXA/viewform?usp=dialog).

If you have feature requests or bug reports, you can [create an issue](https://github.com/foundation50/classroom50/issues/new/choose) or [contribute code of your own](https://github.com/foundation50/classroom50/blob/main/CONTRIBUTING.md). And if you have questions about Classroom 50, visit our [discussion forum](https://github.com/foundation50/classroom50/discussions) where you can join or start a discussion to talk with the Fifty Foundation's team and with other teachers!

---

## Thread 1 — @tomastrivino (2026-07-01)

<!-- Thank you! Are there any plans to support other languages (i.e. spanis -->

Thank you! Are there any plans to support other languages (i.e. spanish?)

**Reply — @kolbashj (2026-07-02):**

or Rust :)

**Reply — @iamabutalha (2026-07-02):**

or Golang :)

**Reply — @LuisMUtec (2026-07-03):**

Same question here. I'd also be interested in helping bring Spanish support to Classroom 50

**Reply — @rongxin-liu (2026-07-03):**

@tomastrivino @LuisMUtec We recently added localization support, so the Spanish version is available at: https://classroom50.org/?lang=es

**Reply — @tomastrivino (2026-07-03):**

Thanks, appreciate it!

**Reply — @Snehashri52 (2026-07-07):**

This is a great initiative for educators and students. Open-source tools like Classroom 50 can make programming education more accessible by simplifying assignment management, automated grading, and Git-based workflows. Having both a web interface and CLI option is especially useful for different teaching environments. Looking forward to seeing how the community contributes new features and improvements to make coding education more efficient and collaborative.

---

## Thread 2 — @mjmay-kinneret (2026-07-02)

<!-- Looking forward to trying Classroom 50.  I've been using GitHub Classr -->

Looking forward to trying Classroom 50.  I've been using GitHub Classroom for years to manage and autograde assignments.  Will there be any training sessions that are not on a Friday afternoon?

**Reply — @dmalan (2026-07-03):**

Just the Friday live sessions, but we'll post a recording of at least one!

https://github.com/foundation50/classroom50/wiki#training-sessions

---

## Thread 3 — @pas-mllr (2026-07-02)

<!-- Looks good! But is it really necessary for the tool to have full read  -->

Looks good! But is it really necessary for the tool to have full read and write access to all users' private and public repo's?

**Reply — @rongxin-liu (2026-07-03):**

Yes, it is. Please see: https://github.com/foundation50/classroom50/discussions/34

---

## Thread 4 — @jmaxwell1957 (2026-07-17)

<!-- Can not link to GitHub organization either via web or cli interfaces.  -->

Can not link to GitHub organization either via web or cli interfaces. Options are greyed in web and flags are unknown with cli. Frustrating.

**Reply — @rongxin-liu (2026-07-17):**

Minding sending screenshots and file a bug report at https://github.com/foundation50/classroom50/issues?

---

## Thread 5 — @ProfSamScott (2026-07-20)

<!-- I have registered for a training session but I can't find any informat -->

I have registered for a training session but I can't find any information on how to access the session. How do I participate? Thanks!

**Reply — @brianyu28 (2026-07-20):**

If you've registered for this week's session, you'll receive an email early this week with details on how to access the session!

---

## Thread 6 — @bmahalakshmi2612 (2026-07-24)

<!-- This account is my private account, i already created github account u -->

This account is my private account, i already created github account under my organisation but I lost my recovery codes that's why I can't open that git hub account which comes under the organisation. what can we do? did we get new recovery code

**Reply — @dmalan (2026-07-24):**

Afraid that sounds like a question for https://support.github.com/!

---

## Thread 7 — @jaguardado123 (2026-07-26)

<!-- It seems the website has been down since this morning. Is there any up -->

It seems the website has been down since this morning. Is there any update on when it may be back up?

**Reply — @rongxin-liu (2026-07-26):**

Classroom 50 is hosted through GitHub Pages, and it doesn't seem to be an issue on our end. https://githubstatus.com is all green.

Where are you located, and who is your internet service provider? What browser were you using?

**Reply — @jaguardado123 (2026-07-26):**

I am located in Texas, USA, my internet provider is Spectrum and I've tried multiple browsers. 
I'm realizing now the website may be blocked. My students can not access their assignments either and we are getting similar errors.
I'm attaching a screenshot of the browser response.
<img width="400"  alt="classroom50" src="https://github.com/user-attachments/assets/53af65a1-5620-4604-9b78-2adc94a472f7" />

**Reply — @rongxin-liu (2026-07-26):**

Are you and your students accessing classroom50.org on campus, or are they also getting the same error at home?

**Reply — @jaguardado123 (2026-07-26):**

I believe they are attempting to access from home as well. I have not attempted to access from campus yet.

**Reply — @rongxin-liu (2026-07-26):**

We just checked, and it looks like your ISP, Spectrum, is indeed blocking our website `classroom50.org`.

Please try submitting a request to unblock the website: https://www.spectrum.net/support/forms/verify_url_security

**Reply — @jaguardado123 (2026-07-26):**

The website is still available on-campus so I will notify students to accept assignments while on campus for the time being.
I will submit a request to Spectrum then.
Thank you!!

**Reply — @rongxin-liu (2026-07-26):**

We also submitted the request, so hopefully Spectrum can unblock us soon.

**Reply — @jaguardado123 (2026-07-27):**

Spectrum unblocked your website a few hours ago.
Thank you so much for your help!!

---

## Thread 8 — @lingdoc (2026-07-26)

<!-- I am just testing this out again. I've created a new repo and synced i -->

I am just testing this out again. I've created a new repo and synced it with Classroom 50. all permissions are set to "no permission" for new members, which I thought would make all organization repos invisible. However, when I add a new user to the classroom, all repos (including private templates) are visible. Do you know why this is happening?

**Reply — @rongxin-liu (2026-07-26):**

Would you mind walking us through how you set up Classroom 50 in more detail? Do you mean that you created a new organization, configured it through https://classroom50.org, and set the organization’s base permissions to No permissions, yet regular members of your organization were still able to see all private repositories? Was the user you invited to your organization given "member" or "owner" permissions?

**Reply — @lingdoc (2026-07-26):**

yes, exactly. actually, it looks like the user I added can see their own repository and any template repositories. They cannot see any other private repos (that are not templates). i've made some private repositories templates so I can use them as the base for assignments. maybe I need to change visibility of the template repo itself..?

**Reply — @rongxin-liu (2026-07-26):**

Thanks for the clarification. A few things are worth knowing:

1. When you invite students to your classroom, Classroom 50 (using your GitHub token) sends them a GitHub Team invitation. Once they accept the invitation, they are added to a classroom-specific GitHub team (i.e., the student team).
2. When you create an assignment using a template repository (whether private or public), Classroom 50 automatically grants the student team read access to the template repository. This allows students to create their assignment repositories from the contents of the template when they accept the assignment.

If I understand the problem correctly, you've already created a few assignments through Classroom 50 using template repositories? If that's the case, your students would be able to see those private template repositories because the student team has been granted `read` access to them.

If you create a new private template repository in your organization now, but don't create an assignment that references it through Classroom 50, your students shouldn't be able to see that repository because the student team hasn’t been granted access to it yet.

**Reply — @lingdoc (2026-07-26):**

when I look at access permissions on the template repo, it seems the Classroom 50 classroom has "direct access" to the repo (I assume to be able to copy it as a template), and so do any members:
<img width="1032" height="707" alt="Screenshot 2026-07-26 at 10 19 00 PM" src="https://github.com/user-attachments/assets/5ab8197d-4eee-4c00-bb81-8a11266e3522" />

**Reply — @lingdoc (2026-07-26):**

OK, so this is different from the old system, where only the repositories created by the students themselves were visible to the students. Is there any way to change this behavior so that the repo is created by the CS50 classroom and then assigned to the student?

**Reply — @rongxin-liu (2026-07-26):**

It is possible to do it this way, but it requires the teacher to know all students' GitHub usernames beforehand. If new students join the class later, the teacher would need to create the missing assignment repositories for them, which places an additional burden on the teacher.

Since Classroom 50 does not have a server running, we grant the student team read access to the private template repository in advance so that students can create their assignment repositories. Without that access, students would not be able to create an assignment repository from the private template because they would not have permission to view its contents.

Are you suggesting that, instead of allowing students to see all assignments (created through Classroom 50) immediately, you would prefer an option to release assignments individually so that students can see them only after they are released? In other words, you would still like to create assignments in advance using private template repositories, but the student team would not be granted access until each assignment is released.

**Reply — @lingdoc (2026-07-26):**

> Are you suggesting that, instead of allowing students to see all assignments (created through Classroom 50) immediately, you would prefer an option to release assignments individually so that students can see them only after they are released? In other words, you would still like to create assignments in advance using private template repositories, but the student team would not be granted access until each assignment is released.

Yes, sort of. I basically don't want them to see the template repo, so they don't get confused (this is an introductory programming course). I'm wondering if there's a way to give them access to create their own repo, but once it's created have a hook that revokes access to the template repo while preserving their access to the individual repo.

**Reply — @rongxin-liu (2026-07-26):**

I see. I would say this is more of a limitation of Classroom 50. Since it does not have a server, a webhook-based approach would not work. For example, we cannot trigger server-side logic to revoke a student's access to the template immediately after they create the assignment repository.

**Reply — @lingdoc (2026-07-27):**

is there an action I could set up on Github that would do something similar?

---

## Thread 9 — @dfkotz (2026-08-28)

<!-- I missed both training sessions.  Where can I find a recording? -->

I missed both training sessions.  Where can I find a recording?

**Reply — @rongxin-liu (2026-08-28):**

Recordings are available here: https://github.com/foundation50/classroom50/wiki#classroom-50
