# coding=utf-8
import inspect

from kataja.singletons import log, ctrl
from kataja.KatajaAction import KatajaAction


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


class Help(KatajaAction):
    k_action_uid = 'help'
    k_command = 'Help'
    k_undoable = False

    def method(self, command=None):
        """ Dump keyboard shortcuts to console. At some point, make this to use
        dialog window instead.
        :return: None
        """
        if command:
            # command is probably KatajaAction's run_command -method.
            # then we want its 'method' -method's docstring.
            found = False
            for cls in inspect.getmro(command.__self__.__class__):
                if cls.__dict__.get('method', None):
                    #print('----------------------------')
                    print('<b>' + cls.k_action_uid + str(inspect.signature(cls.method))+'</b>')
                    print(f'<i>""" {cls.method.__doc__.replace("    ", " ")} """</i>')
                    found = True
                    break
            if not found:
                print(command.__doc__)
        else:
            d = ctrl.ui.actions
            keys = sorted(list(d.keys()))
            print('---------- Available actions ----------')
            for key in keys:
                my_class = d[key].__class__
                command = getattr(my_class, "k_command", "")
                sig = str(inspect.signature(my_class.method))
                if sig.startswith('(self, '):
                    sig = '(' + sig[7:]
                elif sig == '(self)':
                    sig = '()'
                print(f'<b>{key + sig:.<60}</b> : {command}')
            print('---------------------------------------')
            print('<b>help(method_name)</b> for more information.')

