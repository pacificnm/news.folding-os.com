import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppHeader, useSession } from 'foldingos-ui';
import Home from './pages/Home.jsx';
import Article from './pages/Article.jsx';

export default function App() {
  const { user, loading } = useSession();

  if (loading || user === null) {
    // useSession() redirects to /auth/login on 401; this covers the brief
    // window before that redirect (or the initial fetch) resolves.
    return null;
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <AppHeader appName="News" user={user} />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/article/:id" element={<Article />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
