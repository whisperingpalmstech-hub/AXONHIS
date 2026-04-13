"use client";

import React, { useState, useEffect } from 'react';
import { 
  Calendar, FileText, Activity, CreditCard, 
  Video, LogOut, Bell, User, Clock, TestTube2
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { portalApi } from '@/lib/portal-api';

export default function PatientDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [patientName, setPatientName] = useState<string>('Patient');
  const [data, setData] = useState({
    appointments: [],
    records: [],
    prescriptions: [],
    telemedSessions: [],
    invoices: [],
    encounters: [],
    stats: {
      nextAppointment: 'No upcoming',
      newReports: 0,
      billingDue: '$0.00'
    }
  });

  const [patientId, setPatientId] = useState<string | null>(null);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [selectedEncounter, setSelectedEncounter] = useState<any>(null);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [bookingForm, setBookingForm] = useState({ doctorId: '', date: '', slotId: '', reason: '' });
  const [bookingLoading, setBookingLoading] = useState(false);
  const [toast, setToast] = useState<{message: string, type: 'error' | 'success'} | null>(null);
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);

  const showToast = (message: string, type: 'error' | 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem("patient_token");
    const storedPatientId = localStorage.getItem("patient_id");
    
    if (!token || !storedPatientId) {
      router.push("/login");
      return;
    }
    
    setPatientId(storedPatientId);
  }, [router]);

  useEffect(() => {
    if (bookingForm.doctorId && bookingForm.date) {
      portalApi.getDoctorSlots(bookingForm.doctorId, bookingForm.date)
        .then(res => setAvailableSlots(Array.isArray(res) ? res : []))
        .catch(() => setAvailableSlots([]));
    } else {
      setAvailableSlots([]);
    }
  }, [bookingForm.doctorId, bookingForm.date]);

  useEffect(() => {
    if (!patientId) return;

    const fetchData = async () => {
      try {
        const [info, apts, labs, rx, docList, telemed, bills, encList] = await Promise.all([
          portalApi.getPatientInfo(patientId),
          portalApi.getMyAppointments(patientId),
          portalApi.getLabResults(patientId),
          portalApi.getPrescriptions(patientId),
          portalApi.getDoctors(patientId),
          portalApi.getTelemedicineSessions(patientId),
          portalApi.getInvoices(patientId),
          portalApi.getEncounters(patientId)
        ]);

        setDoctors(Array.isArray(docList) ? docList : []);
        setPatientName(`${info.first_name || 'Patient'} ${info.last_name || ''}`);
        
        const invoiceData = Array.isArray(bills) ? bills : [];
        const totalDue = invoiceData.reduce((sum, inv) => sum + (inv.amount_due || 0), 0);

        setData({
          appointments: Array.isArray(apts) ? apts.slice(0, 3) : [],
          records: Array.isArray(labs) ? labs.slice(0, 3) : [],
          prescriptions: Array.isArray(rx) ? rx.slice(0, 3) : [],
          encounters: Array.isArray(encList) ? encList.slice(0, 5) : [],
          telemedSessions: Array.isArray(telemed) ? telemed : [],
          invoices: invoiceData,
          stats: {
            nextAppointment: apts[0]?.appointment_time ? new Date(apts[0].appointment_time).toLocaleString() : 'No upcoming',
            newReports: Array.isArray(labs) ? labs.length : 0,
            billingDue: `$${totalDue.toFixed(2)}`
          }
        });
      } catch (err) {
        console.error("Failed to load portal data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [patientId]);

  const handleBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId || !bookingForm.doctorId || !bookingForm.slotId) {
      showToast("Please fill in all required fields and select an available time slot.", "error");
      return;
    }
    
    // Find slot to reconstruct appointment time conceptually
    const tgtSlot = availableSlots.find(s => s.id === bookingForm.slotId);
    let appTimeStr = new Date().toISOString(); // fallback
    if (tgtSlot && bookingForm.date) {
      appTimeStr = new Date(`${bookingForm.date}T${tgtSlot.start_time}`).toISOString();
    }
    
    setBookingLoading(true);
    try {
      await portalApi.bookAppointment({
        patient_id: patientId,
        doctor_id: bookingForm.doctorId,
        appointment_time: appTimeStr,
        slot_id: bookingForm.slotId,
        type: 'in_person',
        reason: bookingForm.reason
      });
      showToast("Appointment booked successfully!", "success");
      setShowBookingModal(false);
      setBookingForm({ doctorId: '', date: '', slotId: '', reason: '' });
      // Quickly refetch data
      const apts = await portalApi.getMyAppointments(patientId);
      setData(prev => ({ ...prev, appointments: apts }));
    } catch (err: any) {
      console.error(err);
      showToast(err.message || "An error occurred while booking the appointment.", "error");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* SIDEBAR */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-200 p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-xl">
            A
          </div>
          <span className="text-xl font-bold tracking-tight">Patient Portal</span>
        </div>

        <nav className="flex-1 space-y-2">
          {[
            { id: 'overview', label: 'Dashboard', icon: Activity },
            { id: 'appointments', label: 'Appointments', icon: Calendar },
            { id: 'records', label: 'Medical Records', icon: FileText },
            { id: 'telemed', label: 'Telemedicine', icon: Video },
            { id: 'billing', label: 'Billing & Payments', icon: CreditCard },
            { id: 'qa', label: 'QA Testing', icon: TestTube2, action: () => router.push('/qa') },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeTab === item.id 
                  ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-sm' 
                  : 'text-slate-500 hover:bg-slate-100'
              }`}
            >
              <item.icon size={20} />
              {item.label}
            </button>
          ))}
        </nav>

        <button 
          onClick={() => {
            localStorage.clear();
            router.push("/login");
          }}
          className="mt-auto flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl transition-all"
        >
          <LogOut size={20} />
          Sign Out
        </button>
      </aside>

      {/* MAIN CONTENT */}
      <main className="ml-64 p-10 max-w-7xl">
        <header className="flex justify-between items-center mb-10">
          <div className="flex-1">
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Welcome, {patientName}</h1>
            <p className="text-slate-500 mt-1">Managing your health at AxonHIS</p>
          </div>
          <div className="flex gap-4">
            <button className="p-3 bg-white border border-slate-200 rounded-xl hover:shadow-md transition-shadow relative">
              <Bell size={20} className="text-slate-600" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
              <div className="text-right">
                <p className="text-sm font-bold">{patientName}</p>
                <p className="text-[10px] text-indigo-600 font-mono uppercase font-bold">Patient ID: {patientId ? patientId.substring(0,8).toUpperCase() : 'N/A'}</p>
              </div>
              <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-700">
                <User size={20} />
              </div>
            </div>
          </div>
        </header>

        {activeTab === 'overview' && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                { label: 'Next Appointment', value: data.stats.nextAppointment, icon: Calendar, color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Total Records', value: `${data.stats.newReports} Items`, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                { label: 'Billing Due', value: data.stats.billingDue, icon: CreditCard, color: 'text-amber-600', bg: 'bg-amber-50' },
                { label: 'Prescriptions', value: `${data.prescriptions.length} Active`, icon: Activity, color: 'text-purple-600', bg: 'bg-purple-50' },
              ].map((stat, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className={`w-10 h-10 ${stat.bg} ${stat.color} rounded-lg flex items-center justify-center mb-4`}>
                    <stat.icon size={20} />
                  </div>
                  <p className="text-sm text-slate-500 font-medium">{stat.label}</p>
                  <p className="text-lg font-extrabold mt-1">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* UPCOMING APPOINTMENTS & RECENT REPORTS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                  <h3 className="font-bold text-lg">Upcoming Appointments</h3>
                  <button className="text-indigo-600 text-sm font-semibold hover:underline">Book New</button>
                </div>
                <div className="divide-y divide-slate-50">
                  {data.appointments.length > 0 ? data.appointments.map((apt: any, i) => (
                    <div key={i} className="p-6 hover:bg-slate-50 transition-colors flex justify-between items-center group">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 group-hover:bg-white transition-colors">
                          <User size={24} />
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{apt.doctor?.first_name ? `Dr. ${apt.doctor.first_name} ${apt.doctor.last_name}` : apt.department}</p>
                          <p className="text-xs text-slate-500">{apt.department} • {apt.appointment_type || 'In-Person'}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-slate-700">{new Date(apt.appointment_time).toLocaleString()}</p>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-slate-100 text-slate-500">
                          {apt.status}
                        </span>
                      </div>
                    </div>
                  )) : (
                    <div className="p-10 text-center text-slate-400">No upcoming appointments</div>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100">
                  <h3 className="font-bold text-lg">Recent Medical Records</h3>
                </div>
                <div className="p-6 space-y-4">
                  {data.records.length > 0 ? data.records.map((record: any, i) => (
                    <div key={i} className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100 group cursor-pointer hover:border-indigo-300 transition-all">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white border border-slate-200 rounded-xl flex items-center justify-center text-indigo-600 shadow-sm group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                          <FileText size={18} />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-900">{record.value} Result</p>
                          <p className="text-[10px] text-slate-500 uppercase font-bold">Lab Report • {new Date(record.entered_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <button className="text-indigo-600 text-xs font-bold bg-white px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">View</button>
                    </div>
                  )) : (
                    <div className="p-10 text-center text-slate-400">No recent medical records</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="animate-in fade-in duration-500 space-y-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">My Appointments</h2>
              <button 
                onClick={() => setShowBookingModal(true)}
                className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold shadow hover:bg-indigo-700 transition"
              >
                + Book New
              </button>
            </div>
            
            <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-500 font-medium text-sm">
                  <tr>
                    <th className="px-6 py-4">Date & Time</th>
                    <th className="px-6 py-4">Department / Doctor</th>
                    <th className="px-6 py-4">Type</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.appointments.length > 0 ? data.appointments.map((apt: any, i) => (
                    <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-semibold text-slate-800">
                        {new Date(apt.appointment_time).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                         <p className="font-bold text-slate-900">{apt.doctor?.first_name ? `Dr. ${apt.doctor.first_name} ${apt.doctor.last_name}` : apt.department || 'General'}</p>
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {apt.appointment_type || 'In-Person'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${apt.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {apt.status || 'Pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => {
                            setBookingForm({ 
                              doctorId: apt.doctor_id || '', 
                              date: '', 
                              slotId: '',
                              reason: `Request to reschedule appointment originally on ${new Date(apt.appointment_time).toLocaleString()}` 
                            });
                            setShowBookingModal(true);
                          }}
                          className="text-indigo-600 font-semibold text-sm hover:underline"
                        >
                          Reschedule
                        </button>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan={5} className="p-8 text-center text-slate-400">No appointments found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'records' && (
          <div className="animate-in fade-in duration-500 space-y-8">
            <h2 className="text-2xl font-bold">Medical Records</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm p-6">
                <h3 className="font-bold text-lg mb-4">Clinical Documents</h3>
                 <div className="space-y-3">
                  {data.encounters?.length > 0 ? data.encounters.map((enc: any, i: number) => (
                    <div key={i} onClick={() => setSelectedEncounter(enc)} className="p-4 border border-slate-100 rounded-xl hover:border-indigo-300 transition-all cursor-pointer group flex justify-between items-center">
                      <div>
                        <p className="font-bold text-slate-800 group-hover:text-indigo-600">{enc.type || 'Visit Summary'}</p>
                        <p className="text-xs text-slate-500 mt-1">{new Date(enc.start_time || Date.now()).toLocaleDateString()}</p>
                      </div>
                      <FileText size={20} className="text-slate-300 group-hover:text-indigo-600" />
                    </div>
                  )) : <p className="text-slate-400 text-center py-4">No documents found.</p>}
                 </div>
              </div>
              <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm p-6">
                <h3 className="font-bold text-lg mb-4">Lab Results</h3>
                 <div className="space-y-3">
                  {data.records.length > 0 ? data.records.map((r: any, i: number) => (
                    <div key={i} className="p-4 border border-slate-100 rounded-xl hover:border-indigo-300 transition-all cursor-pointer group flex justify-between items-center">
                      <div>
                        <p className="font-bold text-slate-800 group-hover:text-indigo-600">{r.test_name || 'Lab Test'} - {r.value}</p>
                        <p className="text-xs text-slate-500 mt-1">{new Date(r.entered_at || Date.now()).toLocaleDateString()}</p>
                      </div>
                      <FileText size={20} className="text-slate-300 group-hover:text-indigo-600" />
                    </div>
                  )) : <p className="text-slate-400 text-center py-4">No lab results available.</p>}
                 </div>
              </div>
              <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm p-6">
                <h3 className="font-bold text-lg mb-4">Active Prescriptions</h3>
                 <div className="space-y-3">
                  {data.prescriptions.length > 0 ? data.prescriptions.map((r: any, i) => (
                    <div key={i} className="p-4 border border-slate-100 rounded-xl flex justify-between items-center bg-blue-50/50">
                      <div>
                        <p className="font-bold text-slate-800">{r.drug_name || 'Medication'}</p>
                        <p className="text-xs text-slate-500 mt-1">{r.dosage || '1 Tablet'} • {r.frequency || 'Daily'}</p>
                      </div>
                      <button className="text-xs font-semibold text-blue-600 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-50">Refill</button>
                    </div>
                  )) : <p className="text-slate-400 text-center py-4">No active prescriptions.</p>}
                 </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'telemed' && (
          <div className="animate-in fade-in duration-500 flex flex-col items-center justify-center p-20 bg-gradient-to-br from-indigo-50 to-white rounded-3xl border border-indigo-100">
            <div className="w-24 h-24 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mb-6 shadow-sm">
              <Video size={40} />
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900 mb-2">Telemedicine Kiosk</h2>
            {data.telemedSessions.length > 0 ? (
              <div className="w-full max-w-2xl mt-6 space-y-4">
                {data.telemedSessions.map((ts: any, i: number) => (
                  <div key={i} className="bg-white p-6 rounded-2xl shadow border border-indigo-100 flex justify-between items-center">
                    <div>
                      <h4 className="font-bold text-lg">Dr. {ts.doctor?.last_name || 'Assigned Doctor'}</h4>
                      <p className="text-slate-500">{new Date(ts.appointment_time).toLocaleString()}</p>
                    </div>
                    <button className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold shadow hover:bg-indigo-700">Join Call</button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 max-w-md text-center mb-8">
                Connect with doctors virtually. You have no active video sessions scheduled for today.
              </p>
            )}
            <button onClick={() => setShowBookingModal(true)} className="mt-4 bg-indigo-600 text-white px-8 py-3 rounded-full font-bold shadow-md hover:bg-indigo-700 transition transform hover:scale-105">
              Book Virtual Consult
            </button>
          </div>
        )}

        {activeTab === 'billing' && (
          <div className="animate-in fade-in duration-500 space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Billing & Payments</h2>
              <div className="bg-amber-50 text-amber-600 px-4 py-2 rounded-lg font-bold text-sm border border-amber-200">
                Total Due: {data.stats.billingDue}
              </div>
            </div>
            {data.invoices.length > 0 ? (
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 {data.invoices.map((inv: any, i: number) => (
                   <div key={i} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col">
                     <div className="flex justify-between items-start mb-4">
                       <div>
                         <h4 className="font-bold text-lg">Invoice #{inv.id?.substring(0,6).toUpperCase()}</h4>
                         <p className="text-sm text-slate-500">{new Date(inv.created_at || inv.date).toLocaleDateString()}</p>
                       </div>
                       <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${inv.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                         {inv.status || 'Unpaid'}
                       </span>
                     </div>
                     <p className="text-2xl font-extrabold text-slate-900 mb-4">${parseFloat(inv.amount_due || '0').toFixed(2)}</p>
                     <button className="mt-auto w-full border border-indigo-200 bg-indigo-50 text-indigo-700 py-2 rounded-xl font-bold hover:bg-indigo-100 transition">Pay Now</button>
                   </div>
                 ))}
               </div>
            ) : (
                <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center">
                   <CreditCard size={48} className="text-slate-300 mx-auto mb-4" />
                   <h3 className="text-xl font-bold text-slate-700 mb-2">No Outstanding Invoices</h3>
                   <p className="text-slate-500">Your account balance is up to date.</p>
                   <button className="mt-6 border border-slate-300 text-slate-600 px-6 py-2 rounded-lg font-semibold hover:bg-slate-50 transition">
                     View Payment History
                   </button>
                </div>
            )}
          </div>
        )}
      </main>

      {/* BOOKING MODAL */}
      {showBookingModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-bold text-xl">Book Appointment</h3>
              <button onClick={() => setShowBookingModal(false)} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
            </div>
            <form onSubmit={handleBooking} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Select Doctor</label>
                <select 
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 transition-all outline-none bg-white"
                  value={bookingForm.doctorId}
                  onChange={(e) => setBookingForm({ ...bookingForm, doctorId: e.target.value })}
                  disabled={doctors.length === 0}
                >
                  <option value="">{doctors.length === 0 ? '-- No doctors available --' : '-- Choose a provider --'}</option>
                  {doctors.map(doc => (
                    <option key={doc.id} value={doc.id}>Dr. {doc.first_name} {doc.last_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Date</label>
                <input 
                  type="date" 
                  required
                  className="w-full border border-slate-200 rounded-xl p-3 bg-slate-50 font-medium"
                  value={bookingForm.date}
                  onChange={e => setBookingForm({...bookingForm, date: e.target.value, slotId: ''})}
                />
              </div>

              {bookingForm.date && bookingForm.doctorId && (
                <div>
                  <label className="block text-sm font-bold text-slate-700 mb-2">Available Time Slots</label>
                  {availableSlots.length === 0 ? (
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-500 text-sm">
                      <Clock size={20} className="mx-auto mb-1 opacity-50" />
                      No available slots matching this date.
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-[120px] overflow-y-auto p-1">
                      {availableSlots.map(slot => (
                        <button
                          key={slot.id}
                          type="button"
                          onClick={() => setBookingForm({...bookingForm, slotId: slot.id})}
                          className={`py-2 px-1 text-sm font-bold rounded-xl border transition-all ${
                            bookingForm.slotId === slot.id 
                              ? 'bg-indigo-600 text-white border-indigo-600 shadow-md transform scale-[1.02]' 
                              : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                          }`}
                        >
                          {slot.start_time?.substring(0, 5)}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">Reason for Visit</label>
                <textarea 
                  rows={2}
                  className="w-full border border-slate-200 rounded-xl p-3 bg-slate-50 font-medium disabled:opacity-50"
                  placeholder="E.g. Routine checkup, fever, etc."
                  value={bookingForm.reason}
                  onChange={e => setBookingForm({...bookingForm, reason: e.target.value})}
                ></textarea>
              </div>
              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setShowBookingModal(false)} className="px-5 py-2.5 font-bold text-slate-600 hover:bg-slate-50 rounded-xl">Cancel</button>
                <button type="submit" disabled={bookingLoading} className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-md disabled:opacity-70 flex items-center gap-2">
                  {bookingLoading ? <Activity size={18} className="animate-spin" /> : 'Confirm Booking'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ENCOUNTER MODAL */}
      {selectedEncounter && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
            <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-100 text-indigo-700 rounded-xl flex items-center justify-center">
                  <FileText size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-xl text-slate-800">Visit Summary</h3>
                  <p className="text-xs text-slate-500 font-mono">{new Date(selectedEncounter.start_time || Date.now()).toLocaleString()}</p>
                </div>
              </div>
              <button onClick={() => setSelectedEncounter(null)} className="text-slate-400 hover:text-slate-600 text-2xl leading-none transition-colors">&times;</button>
            </div>
            
            <div className="p-6 overflow-y-auto bg-white flex-1 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Provider</p>
                  <p className="font-bold text-slate-800">{selectedEncounter.doctor?.first_name ? `Dr. ${selectedEncounter.doctor.first_name} ${selectedEncounter.doctor.last_name}` : 'Attending Physician'}</p>
                  <p className="text-sm text-slate-500 mt-0.5">{selectedEncounter.department || 'General Practice'}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Status / Priority</p>
                  <p className="font-bold text-slate-800 capitalize">{selectedEncounter.status || 'Completed'}</p>
                  <p className="text-sm text-slate-500 mt-0.5 capitalize">{selectedEncounter.priority || 'Routine'}</p>
                </div>
              </div>

              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Chief Complaint / Reason for Visit</p>
                <div className="p-4 bg-white border border-slate-100 rounded-2xl text-slate-700 shadow-sm leading-relaxed">
                  {selectedEncounter.reason || 'Routine follow-up or checkup.'}
                </div>
              </div>

              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Clinical Notes</p>
                <div className="p-4 bg-white border border-slate-100 rounded-2xl text-slate-700 shadow-sm leading-relaxed min-h-[100px]">
                  {selectedEncounter.notes || 'No extensive clinical notes recorded for this encounter.'}
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
              <button 
                onClick={() => {
                  const safeDate = (!selectedEncounter.start_time || selectedEncounter.start_time === "None") ? new Date() : new Date(selectedEncounter.start_time);
                  const validDate = isNaN(safeDate.getTime()) ? new Date() : safeDate;
                  
                  const content = `AxonHIS Encounter Summary\n\nDate: ${validDate.toLocaleString()}\nProvider: ${selectedEncounter.doctor?.first_name ? `Dr. ${selectedEncounter.doctor.first_name} ${selectedEncounter.doctor.last_name}` : 'Attending Physician'}\nDepartment: ${selectedEncounter.department || 'General Practice'}\nStatus: ${selectedEncounter.status || 'Completed'}\n\nChief Complaint:\n${selectedEncounter.reason || 'Routine follow-up or checkup.'}\n\nClinical Notes:\n${selectedEncounter.notes || 'No extensive clinical notes recorded for this encounter.'}`;
                  const blob = new Blob([content], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `Encounter_Summary_${validDate.toISOString().split('T')[0]}.txt`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(url);
                }}
                className="px-5 py-2.5 font-bold text-indigo-600 border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 rounded-xl transition flex items-center gap-2"
              >
                Download File
              </button>
              <button onClick={() => setSelectedEncounter(null)} className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl shadow-md transition">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TOAST NOTIFICATION */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-[100] animate-in slide-in-from-bottom-5 fade-in duration-300">
          <div className={`px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 font-bold ${toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white'}`}>
            {toast.type === 'error' ? <Activity size={20} /> : <FileText size={20} />}
            <p>{toast.message}</p>
            <button onClick={() => setToast(null)} className="ml-4 opacity-70 hover:opacity-100 transition-opacity">&times;</button>
          </div>
        </div>
      )}
    </div>
  );
}
