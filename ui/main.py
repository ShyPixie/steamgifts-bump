#!/usr/bin/env python
#
# Lara Maia <dev@lara.click> 2015 ~ 2016
#
# The Steam Tools is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# The Steam Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#

import gevent
import json
import os
import random

import stlib
import ui


class SteamTools:
    def __init__(self):
        ui.main_window = self
        self.signals = ui.signals.WindowSignals()
        self.config_parser = stlib.config.read()
        self.login_status = ui.logins.Status()

        builder = ui.Gtk.Builder()
        builder.add_from_file('ui/interface.xml')
        builder.connect_signals(self.signals)

        for _object in builder.get_objects():
            if issubclass(type(_object), ui.Gtk.Buildable):
                name = ui.Gtk.Buildable.get_name(_object)
                setattr(self, name, _object)

        self.fake_app_current_game.modify_fg(ui.Gtk.StateFlags.NORMAL, ui.Gdk.color_parse('black'))
        self.fake_app_current_time.modify_fg(ui.Gtk.StateFlags.NORMAL, ui.Gdk.color_parse('black'))

        self.icons_path = 'ui/icons'

        self.steam_icon_available = 'steam_green.png'
        self.steam_icon_busy = 'steam_yellow.png'
        self.steam_icon_unavailable = 'steam_red.png'

        self.steamgifts_icon_available = 'steamgifts_green.png'
        self.steamgifts_icon_busy = 'steamgifts_yellow.png'
        self.steamgifts_icon_unavailable = 'steamgifts_red.png'

        self.steamcompanion_icon_available = 'steamcompanion_green.png'
        self.steamcompanion_icon_busy = 'steamcompanion_yellow.png'
        self.steamcompanion_icon_unavailable = 'steamcompanion_red.png'

        # The tab will not check the signals for the first program start
        # FIXME: Enable the start button manually for now, but we need to check the logins...
        self.start.set_sensitive(True)

        self.main_window.show_all()

        self.select_profile()

        self.spinner.start()
        self.login_status.queue_connect("steam", stlib.steam_check_page)
        self.login_status.queue_connect("steamgifts", stlib.SG_check_page)
        self.login_status.queue_connect("steamcompanion", stlib.SC_check_page)
        self.login_status.wait_queue()
        self.spinner.stop()

    def select_profile(self):
        stlib.config.read()

        if not self.config_parser.has_option('Config', 'chromeProfile'):
            profiles = stlib.browser.get_chrome_profile()

            if not len(profiles):
                self.update_status_bar('I cannot find your chrome/Chromium profile')
                self.new_dialog(ui.Gtk.MesageType.ERROR,
                                'Network Error',
                                'I cannot find your Chrome/Chromium profile',
                                'Some functions will be disabled.')
            elif len(profiles) == 1:
                profile_name = os.path.join(stlib.browser.get_chrome_dir(), profiles[0])
                self.config_parser.set('Config', 'chromeProfile', profile_name)
                stlib.config.write()
            else:
                self.select_profile_dialog.add_button('Ok', 1)

                temp_radiobutton = None
                for i in range(len(profiles)):
                    with open(os.path.join(stlib.browser.get_chrome_dir(), profiles[i], 'Preferences')) as prefs_file:
                        prefs = json.load(prefs_file)

                    try:
                        account_name = prefs['account_info'][0]['full_name']
                    except KeyError:
                        account_name = prefs['profile']['name']

                    profile_name = profiles[i]
                    temp_radiobutton = ui.Gtk.RadioButton.new_with_label_from_widget(temp_radiobutton,
                                                                                     '{} ({})'.format(account_name,
                                                                                                      profile_name))

                    temp_radiobutton.connect('toggled', self.signals.on_select_profile_button_toggled, i)
                    self.radiobutton_box.pack_start(temp_radiobutton, False, False, 0)

                self.select_profile_dialog.show_all()
                self.select_profile_dialog.run()
                self.select_profile_dialog.destroy()

                self.config_parser.set('Config', 'chromeProfile', profiles[ui.browser_profile])
                stlib.config.write()

    def update_status_bar(self, message):
        message_id = random.randrange(500)
        self.status_bar.push(message_id, message)

        return message_id

    def new_dialog(self, msg_type, title, markup, secondary_markup=None):
        dialog = ui.Gtk.MessageDialog(transient_for=self.main_window,
                                      flags=ui.Gtk.DialogFlags.MODAL,
                                      destroy_with_parent=True,
                                      type=msg_type,
                                      buttons=ui.Gtk.ButtonsType.OK,
                                      text=markup)
        dialog.set_title(title)
        dialog.format_secondary_markup(secondary_markup)
        dialog.connect('response', lambda d, _: d.destroy())
        dialog.show()
