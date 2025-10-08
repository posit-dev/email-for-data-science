# This feels like it's more contingent on setting up a cron job or automated
# workflow. The logic on whether or not to send (or who to sent to, etc.) is 
# outside of the email workflow in my eyes. So this example feel better suited for
# a set of OS directives or other script with somewhere to have a conditional send action.
# 
# In the context of Quarto and Connect, if it existed in the output metadata, that seems
# to be only because Connect expects to fire an email, so you have to actively trigger the
# "no email" state. 