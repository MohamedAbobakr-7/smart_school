import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { apiFetch } from '../lib/api'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'

const ROLE_LABELS = {
  ADMIN: 'Administrator',
  TEACHER: 'Teacher',
  STUDENT: 'Student',
  PARENT: 'Parent',
}

export function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const setTokens = useAuthStore((s) => s.setTokens)
  const access = useAuthStore((s) => s.access)
  const refresh = useAuthStore((s) => s.refresh)

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [editMode, setEditMode] = useState(false)

  // Form state
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    address: '',
  })

  useEffect(() => {
    fetchProfile()
  }, [])

  async function fetchProfile() {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/users/me/')
      if (!res.ok) throw new Error('Failed to load profile')
      const data = await res.json()
      setProfile(data)
      setForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
        phone_number: data.phone_number || '',
        address: data.address || '',
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await apiFetch('/users/me/', {
        method: 'PATCH',
        body: form,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const msg = typeof data.detail === 'string'
          ? data.detail
          : Object.values(data).flat().join(', ') || 'Update failed'
        throw new Error(msg)
      }
      const updated = await res.json()
      setProfile(updated)
      setForm({
        first_name: updated.first_name || '',
        last_name: updated.last_name || '',
        email: updated.email || '',
        phone_number: updated.phone_number || '',
        address: updated.address || '',
      })
      // Update the auth store user object so the sidebar/topbar reflect changes
      setTokens(access, refresh)
      // Re-fetch to update the store's user object via login data
      const meRes = await apiFetch('/users/me/')
      if (meRes.ok) {
        const meData = await meRes.json()
        useAuthStore.setState({
          user: {
            ...useAuthStore.getState().user,
            first_name: meData.first_name,
            last_name: meData.last_name,
            email: meData.email,
            phone_number: meData.phone_number,
            address: meData.address,
            photo_url: meData.student_profile?.photo_url || useAuthStore.getState().user?.photo_url,
          },
        })
      }
      setEditMode(false)
      setSuccess('Profile updated successfully!')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function handleCancel() {
    setEditMode(false)
    setError(null)
    setSuccess(null)
    if (profile) {
      setForm({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        phone_number: profile.phone_number || '',
        address: profile.address || '',
      })
    }
  }

  if (loading) {
    return (
      <div className="profile-page">
        <PageHeader title="My Profile" subtitle="Loading…" />
        <div className="profile-skeleton">
          <div className="profile-skeleton-line" />
          <div className="profile-skeleton-line" />
          <div className="profile-skeleton-line" />
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="profile-page">
        <PageHeader title="My Profile" />
        <Card>
          <p className="muted">Could not load profile data.</p>
          {error && <p style={{ color: '#ef4444' }}>{error}</p>}
        </Card>
      </div>
    )
  }

  const roleLabel = ROLE_LABELS[profile.role] || profile.role_display || profile.role
  const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(' ') || profile.username

  return (
    <div className="profile-page">
      <PageHeader title="My Profile" subtitle={`${roleLabel} account`} />

      {error && !editMode && (
        <div className="profile-toast profile-toast-error">{error}</div>
      )}
      {success && (
        <div className="profile-toast profile-toast-success">{success}</div>
      )}

      {/* ── Avatar + Identity Card ─────────────────────────────────────── */}
      <Card className="profile-identity-card">
        <div className="profile-identity">
          {profile.student_profile?.photo_url ? (
            <img
              className="profile-avatar profile-avatar-photo"
              src={profile.student_profile.photo_url}
              alt={fullName}
            />
          ) : (
            <div className="profile-avatar">
              {fullName.charAt(0).toUpperCase()}
            </div>
          )}
          <div className="profile-identity-text">
            <h2 className="profile-identity-name">{fullName}</h2>
            <span className="profile-identity-role">{roleLabel}</span>
            <span className="profile-identity-username">@{profile.username}</span>
          </div>
          {!editMode && (
            <button
              type="button"
              className="btn btn-primary profile-edit-btn"
              onClick={() => { setEditMode(true); setSuccess(null); setError(null); }}
            >
              ✏️ Edit Profile
            </button>
          )}
        </div>
      </Card>

      {/* ── Editable Fields ────────────────────────────────────────────── */}
      {editMode ? (
        <Card className="profile-form-card">
          <form onSubmit={handleSave} className="profile-form">
            <div className="profile-form-grid">
              <div className="profile-field">
                <label className="profile-field-label" htmlFor="pf-first">First Name</label>
                <input
                  id="pf-first"
                  type="text"
                  className="profile-field-input"
                  value={form.first_name}
                  onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  disabled={saving}
                />
              </div>
              <div className="profile-field">
                <label className="profile-field-label" htmlFor="pf-last">Last Name</label>
                <input
                  id="pf-last"
                  type="text"
                  className="profile-field-input"
                  value={form.last_name}
                  onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  disabled={saving}
                />
              </div>
              <div className="profile-field">
                <label className="profile-field-label" htmlFor="pf-email">Email</label>
                <input
                  id="pf-email"
                  type="email"
                  className="profile-field-input"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  disabled={saving}
                />
              </div>
              <div className="profile-field">
                <label className="profile-field-label" htmlFor="pf-phone">Phone Number</label>
                <input
                  id="pf-phone"
                  type="text"
                  className="profile-field-input"
                  value={form.phone_number}
                  onChange={(e) => setForm((f) => ({ ...f, phone_number: e.target.value }))}
                  disabled={saving}
                />
              </div>
              <div className="profile-field profile-field-full">
                <label className="profile-field-label" htmlFor="pf-address">Address</label>
                <textarea
                  id="pf-address"
                  className="profile-field-input profile-field-textarea"
                  value={form.address}
                  onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                  disabled={saving}
                  rows={3}
                />
              </div>
            </div>
            {error && <p className="profile-form-error">{error}</p>}
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={handleCancel} disabled={saving}>
                Cancel
              </button>
            </div>
          </form>
        </Card>
      ) : (
        <Card className="profile-details-card">
          <h2 className="profile-section-title">Personal Information</h2>
          <div className="profile-details-grid">
            <div className="profile-detail">
              <span className="profile-detail-label">First Name</span>
              <span className="profile-detail-value">{profile.first_name || '—'}</span>
            </div>
            <div className="profile-detail">
              <span className="profile-detail-label">Last Name</span>
              <span className="profile-detail-value">{profile.last_name || '—'}</span>
            </div>
            <div className="profile-detail">
              <span className="profile-detail-label">Email</span>
              <span className="profile-detail-value">{profile.email || '—'}</span>
            </div>
            <div className="profile-detail">
              <span className="profile-detail-label">Phone</span>
              <span className="profile-detail-value">{profile.phone_number || '—'}</span>
            </div>
            <div className="profile-detail profile-detail-full">
              <span className="profile-detail-label">Address</span>
              <span className="profile-detail-value">{profile.address || '—'}</span>
            </div>
          </div>
        </Card>
      )}

    </div>
  )
}