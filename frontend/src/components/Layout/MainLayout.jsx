import React from 'react';

export const MainLayout = ({ children }) => {
    return (
        <div className="h-screen w-screen overflow-y-auto max-h-[100vh] mb-12 overflow-x-hidden">
        {children}
        </div>
    );
};
