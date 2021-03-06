import threading
import logging
import sys
import time
import os
import json
from datetime import datetime

from PyQt5 import QtCore, QtGui, uic, QtWidgets

from config import Config
from nodes import Nodes

import ui_pb2

DIALOG_UI_PATH = "%s/../res/preferences.ui" % os.path.dirname(sys.modules[__name__].__file__)
class PreferencesDialog(QtWidgets.QDialog, uic.loadUiType(DIALOG_UI_PATH)[0]):

    CFG_DEFAULT_ACTION   = "global/default_action"
    CFG_DEFAULT_DURATION = "global/default_duration"
    CFG_DEFAULT_TARGET   = "global/default_target"
    CFG_DEFAULT_TIMEOUT  = "global/default_timeout"
    
    LOG_TAG = "[Preferences] "
    _notification_callback = QtCore.pyqtSignal(ui_pb2.NotificationReply)

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent, QtCore.Qt.WindowStaysOnTopHint)

        self._cfg = Config.get()
        self._nodes = Nodes.instance()

        self._notification_callback.connect(self._cb_notification_callback)
        self._notifications_sent = {}

        self.setupUi(self)

        self._accept_button = self.findChild(QtWidgets.QPushButton, "acceptButton")
        self._accept_button.clicked.connect(self._cb_accept_button_clicked)
        self._apply_button = self.findChild(QtWidgets.QPushButton, "applyButton")
        self._apply_button.clicked.connect(self._cb_apply_button_clicked)
        self._cancel_button = self.findChild(QtWidgets.QPushButton, "cancelButton")
        self._cancel_button.clicked.connect(self._cb_cancel_button_clicked)

        self._default_timeout_button = self.findChild(QtWidgets.QSpinBox, "spinUITimeout")
        self._default_action_combo = self.findChild(QtWidgets.QComboBox, "comboUIAction")
        self._default_target_combo = self.findChild(QtWidgets.QComboBox, "comboUITarget")
        self._default_duration_combo = self.findChild(QtWidgets.QComboBox, "comboUIDuration")
        self._dialog_pos_combo = self.findChild(QtWidgets.QComboBox, "comboUIDialogPos")

        self._nodes_combo = self.findChild(QtWidgets.QComboBox, "comboNodes")
        self._node_action_combo = self.findChild(QtWidgets.QComboBox, "comboNodeAction")
        self._node_duration_combo = self.findChild(QtWidgets.QComboBox, "comboNodeDuration")
        self._node_monitor_method_combo = self.findChild(QtWidgets.QComboBox, "comboNodeMonitorMethod")
        self._node_loglevel_combo = self.findChild(QtWidgets.QComboBox, "comboNodeLogLevel")
        self._node_intercept_unknown_check = self.findChild(QtWidgets.QCheckBox, "checkInterceptUnknown")
        self._node_name_label = self.findChild(QtWidgets.QLabel, "labelNodeName")
        self._node_version_label = self.findChild(QtWidgets.QLabel, "labelNodeVersion")

        self._node_apply_all_check = self.findChild(QtWidgets.QCheckBox, "checkApplyToNodes")

    def showEvent(self, event):
        super(PreferencesDialog, self).showEvent(event)
        
        try:
            self._reset_status_message()
            self._hide_status_label()
            self._nodes_combo.clear()

            self._node_list = self._nodes.get()
            for addr in self._node_list:
                self._nodes_combo.addItem(addr)

            if len(self._node_list) == 0:
                self._reset_node_settings()
        except Exception as e:
            print(self.LOG_TAG + "exception loading nodes", e)

        self._load_settings()
        
        # connect the signals after loading settings, to avoid firing
        # the signals
        self._nodes_combo.currentIndexChanged.connect(self._cb_node_combo_changed)
        self._node_action_combo.currentIndexChanged.connect(self._cb_node_needs_update)
        self._node_duration_combo.currentIndexChanged.connect(self._cb_node_needs_update)
        self._node_monitor_method_combo.currentIndexChanged.connect(self._cb_node_needs_update)
        self._node_loglevel_combo.currentIndexChanged.connect(self._cb_node_needs_update)
        self._node_intercept_unknown_check.clicked.connect(self._cb_node_needs_update)
        self._node_apply_all_check.clicked.connect(self._cb_node_needs_update)
    
        # True when any node option changes
        self._node_needs_update = False

    def _load_settings(self):
        self._default_action = self._cfg.getSettings(self.CFG_DEFAULT_ACTION)
        self._default_duration = self._cfg.getSettings(self.CFG_DEFAULT_DURATION)
        self._default_target = self._cfg.getSettings(self.CFG_DEFAULT_TARGET)
        self._default_timeout = self._cfg.getSettings(self.CFG_DEFAULT_TIMEOUT)

        self._default_duration_combo.setCurrentText(self._default_duration)
        self._default_action_combo.setCurrentText(self._default_action)
        self._default_target_combo.setCurrentIndex(int(self._default_target))
        self._default_timeout_button.setValue(int(self._default_timeout))

        self._load_node_settings()

    def _load_node_settings(self):
        addr = self._nodes_combo.currentText()
        if addr != "":
            try:
                node_data = self._node_list[addr]['data']
                self._node_version_label.setText(node_data.version)
                self._node_name_label.setText(node_data.name)
                self._node_loglevel_combo.setCurrentIndex(node_data.logLevel)

                node_config = json.loads(node_data.config)
                self._node_action_combo.setCurrentText(node_config['DefaultAction'])
                self._node_duration_combo.setCurrentText(node_config['DefaultDuration'])
                self._node_monitor_method_combo.setCurrentText(node_config['ProcMonitorMethod'])
                self._node_intercept_unknown_check.setChecked(node_config['InterceptUnknown'])
                self._node_loglevel_combo.setCurrentIndex(int(node_config['LogLevel']))
            except Exception as e:
                print(self.LOG_TAG + "exception loading config: ", e)

    def _reset_node_settings(self):
        self._node_action_combo.setCurrentIndex(0)
        self._node_duration_combo.setCurrentIndex(0)
        self._node_monitor_method_combo.setCurrentIndex(0)
        self._node_intercept_unknown_check.setChecked(False)
        self._node_loglevel_combo.setCurrentIndex(0)
        self._node_name_label.setText("")
        self._node_version_label.setText("")

    def _save_settings(self):
        self._show_status_label()
        self._set_status_message("Applying configuration...")

        if self.tabWidget.currentIndex() == 0:
            self._cfg.setSettings(self.CFG_DEFAULT_ACTION, self._default_action_combo.currentText())
            self._cfg.setSettings(self.CFG_DEFAULT_DURATION, self._default_duration_combo.currentText())
            self._cfg.setSettings(self.CFG_DEFAULT_TARGET, self._default_target_combo.currentIndex())
            self._cfg.setSettings(self.CFG_DEFAULT_TIMEOUT, self._default_timeout_button.value())
        
        elif self.tabWidget.currentIndex() == 1:
            addr = self._nodes_combo.currentText()
            if (self._node_needs_update or self._node_apply_all_check.isChecked()) and addr != "":
                try:
                    notif = ui_pb2.Notification(
                            id=int(str(time.time()).replace(".", "")),
                            type=ui_pb2.CHANGE_CONFIG,
                            data="",
                            rules=[])
                    if self._node_apply_all_check.isChecked():
                        for addr in self._nodes.get_nodes():
                            notif.data = self._load_node_config(addr)
                            self._nodes.save_node_config(addr, notif.data)
                            nid = self._nodes.send_notification(addr, notif, self._notification_callback)
                    else:
                        notif.data = self._load_node_config(addr)
                        self._nodes.save_node_config(addr, notif.data)
                        nid = self._nodes.send_notification(addr, notif, self._notification_callback)

                    self._notifications_sent[nid] = notif
                except Exception as e:
                    print(self.LOG_TAG + "exception saving config: ", e)
        
            self._node_needs_update = False

    def _load_node_config(self, addr):
        node_config = json.loads(self._nodes.get_node_config(addr))
        node_config['DefaultAction'] = self._node_action_combo.currentText()
        node_config['DefaultDuration'] = self._node_duration_combo.currentText()
        node_config['ProcMonitorMethod'] = self._node_monitor_method_combo.currentText()
        node_config['LogLevel'] = self._node_loglevel_combo.currentIndex()
        node_config['InterceptUnknown'] = self._node_intercept_unknown_check.isChecked()
        return json.dumps(node_config)

    def _hide_status_label(self):
        self.statusLabel.hide()

    def _show_status_label(self):
        self.statusLabel.show()

    def _set_status_error(self, msg):
        self.statusLabel.setStyleSheet('color: red')
        self.statusLabel.setText(msg)

    def _set_status_successful(self, msg):
        self.statusLabel.setStyleSheet('color: green')
        self.statusLabel.setText(msg)

    def _set_status_message(self, msg):
        self.statusLabel.setStyleSheet('color: darkorange')
        self.statusLabel.setText(msg)

    def _reset_status_message(self):
        self.statusLabel.setText("")

    @QtCore.pyqtSlot(ui_pb2.NotificationReply)
    def _cb_notification_callback(self, reply):
        #print(self.LOG_TAG, "Config notification received: ", reply.id, reply.code)
        if reply.id in self._notifications_sent:
            if reply.code == ui_pb2.OK:
                self._set_status_successful("Configuration applied.")
            else:
                self._set_status_error("Error applying configuration: %s" % reply.data)

            del self._notifications_sent[reply.id]

    def _cb_accept_button_clicked(self):
        self._save_settings()
        self.accept()

    def _cb_apply_button_clicked(self):
        self._save_settings()
    
    def _cb_cancel_button_clicked(self):
        self.reject()

    def _cb_node_combo_changed(self, index):
        self._load_node_settings()

    def _cb_node_needs_update(self):
        self._node_needs_update = True 
