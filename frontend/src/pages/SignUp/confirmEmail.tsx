import { createClient } from '@supabase/supabase-js';
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

const ConfirmEmail = () => {
  const { search } = useLocation();      // e.g. "?access_token=…&type=signup"
  const navigate = useNavigate();

  useEffect(() => {
    async function finishConfirmation() {
      // This reads the ?access_token=… from the URL, verifies it, and
      // stores the session in localStorage automatically.
      const { error } = await supabase.auth.getSession();

      if (error) {
        console.error('Email confirmation failed:', error.message);
        return;
      }
      // Once confirmed, you can redirect the user to wherever you want:
      navigate('/kyc');
    }
    finishConfirmation();
  }, [search, navigate]);

  return <div>Confirming your email…</div>;
}

export default ConfirmEmail