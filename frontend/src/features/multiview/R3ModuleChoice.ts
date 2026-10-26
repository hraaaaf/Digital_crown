import { authorizeLayout, validLayout, type Layout, type ModuleKey, type WorkspaceContext } from './studioLayouts';

/** Only modules with existing authenticated, read-only Cabinet adapters.
 * The nine roadmap presets remain disabled until each declared clinical adapter
 * has its own proof. The selection is volatile, never written to browser storage.
 */
export const R3_REAL_MODULES = ['dossier', 'imagerie', 'suivi', 'agenda'] as const satisfies readonly ModuleKey[];
export const R3_MODULE_LABEL: Readonly<Record<(typeof R3_REAL_MODULES)[number], string>> = {
  dossier:'Dossier', imagerie:'Médias', suivi:'Suivi', agenda:'Agenda',
};

export function chooseR3Module(
  source: Layout,
  slotIndex: number,
  module: ModuleKey,
  context: WorkspaceContext,
): Layout | null {
  if (!validLayout(source) || !['two-columns','two-rows','three-columns','hero-two'].includes(source.geometry) ||
      source.slots.some(slot => slot.access && slot.access !== 'R')) return null;
  if (!Number.isInteger(slotIndex) || slotIndex < 0 || slotIndex >= source.slots.length ||
      !R3_REAL_MODULES.some(candidate => candidate === module) ||
      !context.allowedModules.includes(module) ||
      source.slots.some(slot => !R3_REAL_MODULES.some(candidate => candidate === slot.module))) return null;
  const oldModule = source.slots[slotIndex].module;
  // Choosing an already used module swaps its position, never mounts it twice.
  const slots = source.slots.map((slot,index) => ({
    ...slot,
    module:index===slotIndex ? module : slot.module===module ? oldModule : slot.module,
    access:'R' as const,
  }));
  if (new Set(slots.map(slot => slot.module)).size !== slots.length) return null;
  const proposed: Layout = {...source,slots};
  return authorizeLayout(proposed,context).ok ? proposed : null;
}

export function r3ModuleOptions(layout: Layout, slotIndex: number, context: WorkspaceContext) {
  return R3_REAL_MODULES.filter(module =>
    layout.slots[slotIndex]?.module === module ||
    chooseR3Module(layout,slotIndex,module,context) !== null
  ).filter(module => context.allowedModules.includes(module));
}
