import { ShoppingCart, Store } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { dashboardItemVariants } from '../animations';

export const MarketplaceCard = ({ visible }: { visible: boolean }) => {
  if (!visible) return null;

  return (
    <motion.section variants={dashboardItemVariants}>
      <Link
        to="/approvisionnement"
        className="group relative overflow-hidden flex items-center justify-between gap-5 rounded-elite-lg border border-border-main bg-card-bg/60 backdrop-blur-2xl px-6 py-5 shadow-elite hover:shadow-elite-hover transition-elite"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-white/5 to-transparent pointer-events-none" />
        <div className="relative z-10 flex items-center gap-4 min-w-0">
          <div className="w-12 h-12 rounded-elite-sm bg-primary/10 backdrop-blur-md text-primary border border-primary/15 flex items-center justify-center shrink-0">
            <ShoppingCart size={22} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-widest font-black text-text-muted">Approvisionnement</p>
            <h2 className="text-lg font-black tracking-tight font-outfit text-main" style={{ color: 'var(--text-main)' }}>
              Marketplace
            </h2>
            <p className="text-xs font-medium text-text-muted mt-0.5">Commander les consommables et fournitures du cabinet</p>
          </div>
        </div>
        <Store size={18} className="relative z-10 shrink-0 text-primary transition-transform group-hover:translate-x-1" />
      </Link>
    </motion.section>
  );
};