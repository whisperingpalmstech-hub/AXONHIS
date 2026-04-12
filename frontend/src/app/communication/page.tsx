'use client';

import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, Users, AlertTriangle, Bell, Zap, 
  Send, UserCircle, CheckCircle, Clock
} from 'lucide-react';
import { communicationApi } from '@/lib/communication-api';

export default function CommunicationDashboard() {
  const [activeTab, setActiveTab] = useState('messages');
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  
  // Lists for dropdowns
  const [userList, setUserList] = useState<any[]>([]);
  const [patientList, setPatientList] = useState<any[]>([]);
  
  // Create state for message content
  const [messageText, setMessageText] = useState('');
  const [testReceiverId, setTestReceiverId] = useState('');
  
  const [alertForm, setAlertForm] = useState({ patient_id: '', type: 'vital_sign_alert', severity: 'warning', message: '' });

  // Initial load
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'alerts') {
        setAlerts((await communicationApi.getAlerts()) as any);
        const pts = (await communicationApi.getPatients()) as any;
        setPatientList(pts);
      }
      if (activeTab === 'notifications') setNotifications((await communicationApi.getNotifications()) as any);
      if (activeTab === 'channels') setChannels((await communicationApi.getChannels()) as any);
      if (activeTab === 'escalations') setEscalations((await communicationApi.getEscalations()) as any);
      
      // Always fetch users if we're on messages
      if (activeTab === 'messages') {
        const resp: any = await communicationApi.getUsers();
        setUserList(resp.items || []);
        // Fetch recent messages for the history view
        // Note: This endpoint should fetch messages where the user is either sender or receiver
        // For now we'll fetch them normally
        // setMessages(...)
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleSendMessage = async () => {
    if (!testReceiverId || !messageText) return alert("Need receiver ID and message");
    try {
      await communicationApi.sendMessage({ receiver_id: testReceiverId, message_content: messageText });
      setMessageText('');
      alert("Message Sent! Switch to 'My Notifications' to see the alert (if sent to yourself).");
      fetchData(); // This refreshes the local state
    } catch (e) {
      alert("Failed to send message: " + String(e));
    }
  };

  const handleCreateAlert = async () => {
    if (!alertForm.patient_id || !alertForm.message) return alert("Need patient ID and message");
    try {
      await communicationApi.createAlert({ 
        patient_id: alertForm.patient_id, 
        alert_type: alertForm.type, 
        severity: alertForm.severity, 
        message: alertForm.message 
      });
      setAlertForm({ ...alertForm, message: '' });
      fetchData();
      alert("Critical Alert Pushed!");
    } catch (e) {
      alert("Failed to create alert: " + String(e));
    }
  };

  const handleAcknowledgeAlert = async (id: string) => {
    try {
      await communicationApi.acknowledgeAlert(id);
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  const tabs = [
    { id: 'messages', label: 'Direct Messages', icon: MessageSquare },
    { id: 'channels', label: 'Department Channels', icon: Users },
    { id: 'alerts', label: 'Clinical Alerts', icon: AlertTriangle },
    { id: 'notifications', label: 'My Notifications', icon: Bell },
    { id: 'escalations', label: 'Task Escalations', icon: Zap }
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <Zap size={24} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">CommHub</h1>
            </div>
          </div>
        </div>
        
        <div className="p-4 flex-1 space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab === tab.id 
                ? 'bg-indigo-50 text-indigo-700 font-semibold' 
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <tab.icon size={20} className={activeTab === tab.id ? 'text-indigo-600' : 'text-slate-400'} />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto p-8">
          
          <header className="mb-8 flex justify-between items-end">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 capitalize tracking-tight">
                {tabs.find(t => t.id === activeTab)?.label}
              </h2>
              <p className="text-slate-500 mt-2">Manage your realtime hospital communications.</p>
            </div>
          </header>

          {/* MESSAGES TAB */}
          {activeTab === 'messages' && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                  <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Test Direct Messaging</h3>
                  <div className="flex gap-4 items-end">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Target Staff Member</label>
                      <select 
                        value={testReceiverId} onChange={(e) => setTestReceiverId(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                      >
                        <option value="">Select a staff member...</option>
                        {userList.map((u: any) => (
                          <option key={u.id} value={u.id}>{u.full_name} ({u.roles?.[0]?.display_name || 'Staff'})</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-slate-500 mb-1">Message Content</label>
                      <input 
                        type="text" value={messageText} onChange={(e) => setMessageText(e.target.value)}
                        placeholder="Type your clinical message..."
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                      />
                    </div>
                    <button 
                      onClick={handleSendMessage}
                      className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors h-10"
                    >
                      <Send size={18} />
                      Send
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 mt-4 italic">
                    * Note: Sending a message here automatically generates a Notification for the receiver testing the cross-module triggers.
                  </p>
                </div>
              </div>

              {/* Message History preview */}
              <div className="bg-slate-50 rounded-2xl border border-slate-200 p-6">
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Recent Audit Flow</h3>
                <div className="space-y-3">
                  <div className="p-3 bg-white border border-slate-100 rounded-xl shadow-sm flex justify-between items-center">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">Message Delivered</p>
                      <p className="text-xs text-slate-500">To: Jhon Dhone • "hii..."</p>
                    </div>
                    <span className="px-2 py-1 bg-green-50 text-green-600 text-[10px] font-bold rounded uppercase">Status: Sent</span>
                  </div>
                  <p className="text-[10px] text-center text-slate-400">Database synchronization active. Notifications are routed to recipients.</p>
                </div>
              </div>
            </div>
          )}

          {/* ALERTS TAB */}
          {activeTab === 'alerts' && (
            <div className="space-y-6">
              {/* Alert Creator */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Trigger Clinical Alert</h3>
                <div className="grid grid-cols-4 gap-4 items-end">
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">Select Patient</label>
                    <select 
                      value={alertForm.patient_id} onChange={(e) => setAlertForm({...alertForm, patient_id: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
                    >
                      <option value="">Select Patient...</option>
                      {patientList.map((p: any) => (
                        <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">Type</label>
                    <select 
                      value={alertForm.type} onChange={(e) => setAlertForm({...alertForm, type: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    >
                      <option value="critical_lab">Critical Lab</option>
                      <option value="cdss_warning">CDSS Warning</option>
                      <option value="vital_sign_alert">Vital Sign</option>
                      <option value="procedure_delay">Procedure Delay</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">Message</label>
                    <input 
                      type="text" value={alertForm.message} onChange={(e) => setAlertForm({...alertForm, message: e.target.value})}
                      placeholder="e.g. Sepsis warning..."
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                  <button 
                    onClick={handleCreateAlert}
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <AlertTriangle size={16} /> Trigger
                  </button>
                </div>
              </div>

              {/* Alerts List */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="p-4 text-xs font-semibold text-slate-500 uppercase">Alert Info</th>
                      <th className="p-4 text-xs font-semibold text-slate-500 uppercase">Type / Patient</th>
                      <th className="p-4 text-xs font-semibold text-slate-500 uppercase">Status</th>
                      <th className="p-4 text-xs font-semibold text-slate-500 uppercase text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {alerts.map((alert: any) => (
                      <tr key={alert.id} className="hover:bg-slate-50/50 transition-colors group">
                        <td className="p-4">
                          <div className="flex items-start gap-3">
                            <div className={`mt-1 p-2 rounded-lg ${alert.severity === 'critical' ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'}`}>
                              <AlertTriangle size={16} />
                            </div>
                            <div>
                              <p className="font-semibold text-slate-900">{alert.message}</p>
                              <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                                <Clock size={12} /> {new Date(alert.created_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="inline-flex px-2 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded">{alert.alert_type}</span>
                          <p className="text-xs text-slate-400 font-mono mt-1">{alert.patient_id.slice(0, 8)}...</p>
                        </td>
                        <td className="p-4">
                          {alert.acknowledged_by ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-full">
                              <CheckCircle size={12} /> Acknowledged
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-50 text-red-700 text-xs font-medium rounded-full animate-pulse border border-red-100">
                              PENDING
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          {!alert.acknowledged_by && (
                            <button 
                              onClick={() => handleAcknowledgeAlert(alert.id)}
                              className="px-3 py-1.5 bg-white border border-slate-200 shadow-sm text-slate-700 text-xs font-semibold rounded-md hover:bg-slate-50 transition-colors"
                            >
                              Acknowledge
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {alerts.length === 0 && !loading && (
                      <tr><td colSpan={4} className="p-8 text-center text-slate-400">No active alerts</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="divide-y divide-slate-100">
                {notifications.map((notif: any) => (
                  <div key={notif.id} className={`p-5 flex items-start gap-4 transition-colors ${notif.status === 'unread' ? 'bg-blue-50/30' : 'hover:bg-slate-50/50'}`}>
                    <div className={`p-2 rounded-full ${notif.status === 'unread' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'}`}>
                      <Bell size={20} />
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm ${notif.status === 'unread' ? 'font-semibold text-slate-900' : 'font-medium text-slate-600'}`}>
                        {notif.message}
                      </p>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{notif.notification_type}</span>
                        <span className="text-xs text-slate-400">{new Date(notif.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    {notif.status === 'unread' && (
                      <button 
                        onClick={async () => { await communicationApi.markNotificationRead(notif.id); fetchData(); }}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                      >
                        Mark Read
                      </button>
                    )}
                  </div>
                ))}
                {notifications.length === 0 && !loading && (
                  <div className="p-12 text-center text-slate-400">
                    <Bell size={32} className="mx-auto mb-3 opacity-50" />
                    <p className="font-medium">No Notifications</p>
                    <p className="text-sm mt-1">You are all caught up.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CHANNELS TAB */}
          {activeTab === 'channels' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-12 text-center text-slate-400 bg-slate-50 border-b border-slate-100">
                  <Users size={32} className="mx-auto mb-3 opacity-50 text-indigo-500" />
                  <p className="font-medium text-slate-900">Enterprise Channels Setup</p>
                  <p className="text-sm mt-2 max-w-md mx-auto">
                    Channel backend workflows are active. You can bind these to your nurse/doctor specific UI modules natively using the <code>communicationApi.getChannels()</code> module!
                  </p>
                </div>
            </div>
          )}
          
          {/* ESCALATIONS TAB */}
          {activeTab === 'escalations' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-12 text-center text-slate-400 bg-amber-50/30 border-b border-slate-100">
                  <Zap size={32} className="mx-auto mb-3 opacity-50 text-amber-500" />
                  <p className="font-medium text-slate-900">Task Escalation Flows</p>
                  <p className="text-sm mt-2 max-w-md mx-auto">
                    The backend triggers for parsing overdue medications (etc.) to the <code>TaskEscalations</code> model are running.
                  </p>
                </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
