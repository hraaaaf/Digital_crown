import React from 'react';

/**
 * T1 neutralization shim.
 *
 * The legacy Dashboard tour must never auto-start. Dashboard still mounts this
 * component until the T2 cleanup removes the legacy integration entirely, so
 * keeping a null component here makes the behavioral change explicit and
 * regression-safe without mixing cleanup work into T1.
 */
export const DayOneTour: React.FC = () => null;
