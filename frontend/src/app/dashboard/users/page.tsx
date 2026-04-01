"use client";
import { useTranslation } from "@/i18n";

import React, { useEffect, useState } from "react";
import { Users, Shield, Edit2, Trash2, X, CheckCircle2, AlertCircle } from "lucide-react";

export default function UsersPage() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [selectedUser, setSelectedUser] = useState<any>(null);

  // Form states
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    phone: "",
    role_ids: [] as string[]
  });

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

  function authHeaders() {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/api/v1/auth/users`, { headers: authHeaders() });
      if (!res.ok) throw new Error("Failed to fetch users");
      const data = await res.json();
      setUsers(data.items || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const res = await fetch(`${API}/api/v1/auth/roles`, { headers: authHeaders() });
      if (res.ok) {
        setRoles(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenAdd = () => {
    setModalMode("add");
    setFormData({ email: "", password: "", first_name: "", last_name: "", phone: "", role_ids: [] });
    setShowModal(true);
  };

  const handleOpenEdit = (user: any) => {
    setModalMode("edit");
    setSelectedUser(user);
    setFormData({
      email: user.email,
      password: "", // password not shown
      first_name: user.first_name,
      last_name: user.last_name,
      phone: user.phone || "",
      role_ids: user.roles.map((r: any) => r.id)
    });
    setShowModal(true);
  };

  const handleRoleToggle = (roleId: string) => {
    setFormData(prev => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId) 
        ? prev.role_ids.filter(id => id !== roleId)
        : [...prev.role_ids, roleId]
    }));
  };

  const handleSubmit = async () => {
    try {
      if (modalMode === "add") {
        if (!formData.first_name || !formData.last_name || !formData.email || !formData.password) {
          return alert("Please fill all required fields.");
        }
        if (formData.password.length < 8) {
          return alert("Password must be at least 8 characters long.");
        }

        const payload = { ...formData };
        if (!payload.phone) delete (payload as any).phone;
        
        const res = await fetch(`${API}/api/v1/auth/register`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
          const e = await res.json();
          let errorMsg = "Error creating user";
          if (e.detail && Array.isArray(e.detail)) {
            errorMsg = e.detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('\n');
          } else if (e.detail) {
            errorMsg = typeof e.detail === 'string' ? e.detail : JSON.stringify(e.detail);
          }
          throw new Error(errorMsg);
        }
      } else if (modalMode === "edit" && selectedUser) {
        // Handle role adjustments
        const currentRoleIds = selectedUser.roles.map((r: any) => r.id);
        const newRoleIds = formData.role_ids;

        const rolesToAdd = newRoleIds.filter(id => !currentRoleIds.includes(id));
        const rolesToRemove = currentRoleIds.filter((id: string) => !newRoleIds.includes(id));

        // Add
        for (const rid of rolesToAdd) {
          await fetch(`${API}/api/v1/auth/users/${selectedUser.id}/roles/${rid}`, {
            method: "POST", headers: authHeaders()
          });
        }
        // Remove
        for (const rid of rolesToRemove) {
          await fetch(`${API}/api/v1/auth/users/${selectedUser.id}/roles/${rid}`, {
            method: "DELETE", headers: authHeaders()
          });
        }
      }

      setShowModal(false);
      fetchUsers();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-in fade-in duration-500 rounded-xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
            <Users className="text-blue-600" size={32} />
            {t("users.title")}
          </h1>
          <p className="mt-2 text-slate-500">{t("users.subtitle")}</p>
        </div>
        <button onClick={handleOpenAdd} className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium shadow-md transition-colors flex items-center gap-2">
          <span>+ {t("users.addUser")}</span>
        </button>
      </div>

      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl overflow-hidden min-h-[400px]">
        {loading ? (
          <div className="p-12 text-center text-slate-500">{t("common.loading")}</div>
        ) : error ? (
          <div className="p-12 text-center text-rose-500 bg-rose-50 border border-rose-200 m-4 rounded-xl">{error}</div>
        ) : users.length === 0 ? (
          <div className="p-12 text-center text-slate-500">{t("users.noUsers")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 font-semibold">{t("common.name")}</th>
                  <th className="px-6 py-4 font-semibold">{t("users.role")}</th>
                  <th className="px-6 py-4 font-semibold">{t("users.email")}</th>
                  <th className="px-6 py-4 font-semibold">{t("common.status")}</th>
                  <th className="px-6 py-4 font-semibold text-right">{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center">
                          {u.first_name?.[0]}{u.last_name?.[0]}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900">{u.full_name}</div>
                          <div className="text-slate-500 text-xs mt-0.5 font-mono">ID: {u.id.split('-')[0]}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 mb-1">
                        <Shield size={14} className="text-blue-500" />
                        <span className="font-medium text-slate-700">
                          {u.roles?.length > 0 ? (
                            <div className="flex gap-1 flex-wrap max-w-[200px]">
                              {u.roles.map((r: any) => (
                                <span key={r.id} className="text-[10px] bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">{r.display_name}</span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">No Role Assigned</span>
                          )}
                        </span>
                      </div>
                      {u.two_factor_enabled && <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-md font-medium uppercase mt-1 inline-block">2FA Active</span>}
                    </td>
                    <td className="px-6 py-4 text-slate-600 whitespace-normal min-w-[200px]">
                      <div className="font-medium text-slate-700">{u.email}</div>
                      <div className="text-xs text-slate-400 mt-1">{u.phone || 'No phone'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded badge text-[10px] font-bold ${u.status === 'active' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-rose-100 text-rose-700 border border-rose-200'}`}>
                        {u.status?.toUpperCase() || 'ACTIVE'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => handleOpenEdit(u)} className="p-2 text-slate-400 hover:text-blue-600 transition-colors bg-white hover:bg-blue-50 rounded-lg ml-2 border border-slate-200 shadow-sm">
                        <Edit2 size={14} />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-rose-600 transition-colors bg-white hover:bg-rose-50 rounded-lg ml-2 border border-slate-200 shadow-sm">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CREATE / EDIT USER MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h3 className="text-xl font-bold flex items-center gap-2 text-slate-800">
                {modalMode === "add" ? <Users className="text-blue-600"/> : <Edit2 className="text-blue-600"/>}
                {modalMode === "add" ? t("users.addUser") : `${t("users.editUser")}: ${selectedUser?.full_name}`}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 transition-colors bg-slate-100 hover:bg-slate-200 p-2 rounded-xl"><X size={18} /></button>
            </div>
            
            <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
              
              {modalMode === "add" && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">{t("users.firstName")} <span className="text-red-500">*</span></label>
                      <input type="text" className="w-full border-slate-200 rounded-lg text-sm p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none border transition-all" value={formData.first_name} onChange={e => setFormData(p => ({...p, first_name: e.target.value}))} />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">{t("users.lastName")} <span className="text-red-500">*</span></label>
                      <input type="text" className="w-full border-slate-200 rounded-lg text-sm p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none border transition-all" value={formData.last_name} onChange={e => setFormData(p => ({...p, last_name: e.target.value}))} />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">{t("users.email")} <span className="text-red-500">*</span></label>
                    <input type="email" className="w-full border-slate-200 rounded-lg text-sm p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none border transition-all" value={formData.email} onChange={e => setFormData(p => ({...p, email: e.target.value}))} />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">{t("users.password")} <span className="text-red-500">*</span></label>
                      <input type="text" className="w-full border-slate-200 rounded-lg text-sm p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none border transition-all font-mono" value={formData.password} onChange={e => setFormData(p => ({...p, password: e.target.value}))} />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">{t("users.phone")} ({t("common.optional")})</label>
                      <input type="text" className="w-full border-slate-200 rounded-lg text-sm p-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none border transition-all" value={formData.phone} onChange={e => setFormData(p => ({...p, phone: e.target.value}))} />
                    </div>
                  </div>
                </>
              )}

              {modalMode === "edit" && (
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex gap-3 text-amber-800 text-sm">
                  <AlertCircle size={20} className="flex-shrink-0" />
                  <div>
                    <strong className="block mb-1">Enterprise Access Control</strong>
                    Core identity fields (Name, Email) are secured. You may only bind or unbind operational roles for this user.
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-3">Assign Security Roles</label>
                {roles.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {roles.map(r => (
                      <label key={r.id} className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${formData.role_ids.includes(r.id) ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'}`}>
                        <div className="mt-0.5">
                          <input 
                            type="checkbox" 
                            className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500" 
                            checked={formData.role_ids.includes(r.id)}
                            onChange={() => handleRoleToggle(r.id)}
                          />
                        </div>
                        <div>
                          <p className={`text-sm font-bold ${formData.role_ids.includes(r.id) ? 'text-blue-900' : 'text-slate-700'}`}>{r.display_name}</p>
                          <p className="text-xs text-slate-500 mt-0.5">{r.description || 'System standard role'}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 p-4 bg-slate-50 rounded-lg border border-slate-100 text-center">No roles available in the system.</p>
                )}
              </div>

            </div>
            
            <div className="p-6 border-t border-slate-100 flex justify-end gap-3 bg-slate-50">
              <button onClick={() => setShowModal(false)} className="px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-200 bg-slate-100 rounded-lg transition-colors">{t("common.cancel")}</button>
              <button onClick={handleSubmit} className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-md transition-colors flex items-center gap-2">
                <CheckCircle2 size={16}/> 
                {modalMode === "add" ? t("users.addUser") : t("common.save")}
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
