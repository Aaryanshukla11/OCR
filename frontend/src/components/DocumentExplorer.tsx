import React from 'react';
import { StructuredDataStore } from './StructuredDataStore';

interface DocumentExplorerProps {
  onSelectDocument: (docId: string) => void;
}

export const DocumentExplorer: React.FC<DocumentExplorerProps> = ({ onSelectDocument }) => {
  return <StructuredDataStore onSelectDocument={onSelectDocument} />;
};
