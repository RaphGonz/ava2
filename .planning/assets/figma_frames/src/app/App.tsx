import { Hero } from "./components/Hero";
import { DualPromise } from "./components/DualPromise";
import { MagicMoment } from "./components/MagicMoment";
import { Trust } from "./components/Trust";
import { Pricing } from "./components/Pricing";
import { Footer } from "./components/Footer";

function App() {
  return (
    <main className="w-full min-h-screen bg-black text-white overflow-x-hidden selection:bg-orange-500/30 selection:text-orange-200">
      <Hero />
      <DualPromise />
      <MagicMoment />
      <Trust />
      <Pricing />
      <Footer />
    </main>
  );
}

export default App;
