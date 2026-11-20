import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { RequestModal } from './components/RequestModal';
import { Home } from './pages/Home';
import { DramaDetail } from './pages/DramaDetail';

export const App: React.FC = () => {
  const [isRequestOpen, setIsRequestOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-slate-950 font-sans text-slate-100">
        <Navbar onOpenRequest={() => setIsRequestOpen(true)} />
        
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/drama/:id" element={<DramaDetail />} />
          </Routes>
        </main>

        <footer className="border-t border-slate-900 bg-slate-950/60 py-8 text-center text-xs text-slate-500">
          <p>© 2026 My K-Drama 2.0. Powered by Pyrofork, FastAPI & Google Gemini AI.</p>
        </footer>

        <RequestModal
          isOpen={isRequestOpen}
          onClose={() => setIsRequestOpen(false)}
        />
      </div>
    </BrowserRouter>
  );
};

export default App;
