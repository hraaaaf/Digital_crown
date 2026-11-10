/** Test-only native FUE UI, never linked from active Digital Crown. */
import React from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import { CephPremiumSceneFUEViewer } from '../src/features/ortho/components/CephPremiumSceneFUEViewer'
import { assertSceneFUEDevGate } from '../src/features/ortho/cephPremiumSceneFUEClient'

function FUEApp() {
  const query = new URLSearchParams(window.location.search)
  const patientId = Number(query.get('patient') || '1')
  const studyId = Number(query.get('study') || '1')
  const [connected,setConnected] = React.useState(false)
  const [password,setPassword] = React.useState('')
  const [error,setError] = React.useState('')
  const [loading,setLoading] = React.useState(false)
  try {
    assertSceneFUEDevGate()
    if (!Number.isSafeInteger(patientId) || patientId<1 || !Number.isSafeInteger(studyId) || studyId<1) {
      throw new Error('Identité de fixture synthétique invalide')
    }
  } catch (e) {
    return <main role="alert">FUE isolé refusé : {String(e)}</main>
  }
  const login = async (event:React.FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const form=new URLSearchParams({username:'j21-native-fue@cabinet.invalid',password})
      const response=await axios.post('/api/auth/login',form,{headers:{'Content-Type':'application/x-www-form-urlencoded'},withCredentials:true})
      if (!response.data?.access_token) throw new Error('Authentification JWT refusée')
      localStorage.setItem('token',response.data.access_token)
      setPassword('')
      setConnected(true)
    } catch (e) {setError(e instanceof Error?e.message:'Connexion refusée')}
    finally {setLoading(false)}
  }
  return <main style={{maxWidth:1200,margin:'auto',padding:16}}>
    <header style={{paddingBottom:12,borderBottom:'1px solid #728096'}}>
      <h1 style={{fontSize:22,margin:'0 0 6px'}}>Digital Crown · Céphalo J2.1 · FUE Windows</h1>
      <strong style={{color:'#ffc76a'}}>LAB SYNTHÉTIQUE · PAS UN INSTALLATEUR CERTIFIÉ · AUCUN USAGE CLINIQUE</strong>
    </header>
    {!connected
      ? <form aria-label="Connexion synthétique" onSubmit={e=>void login(e)} style={{display:'grid',gap:12,maxWidth:480,marginTop:18}}>
        <label>Mot de passe fictif <input aria-label="Mot de passe fictif" value={password} onChange={e=>setPassword(e.target.value)}
          type="password" required style={{display:'block',padding:9,width:'100%'}}/></label>
        <button type="submit" disabled={loading} style={{padding:12}}>Connexion JWT réelle (laboratoire)</button>
        {error&&<p role="alert">{error}</p>}
      </form>
      : <CephPremiumSceneFUEViewer patientId={patientId} studyId={studyId}/>}
  </main>
}
createRoot(document.getElementById('root')!).render(<FUEApp/>)
