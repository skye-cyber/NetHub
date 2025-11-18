import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
    Bars3Icon,
    XMarkIcon,
    UserGroupIcon,
    WifiIcon,
    ShieldCheckIcon,
    CogIcon,
    LockClosedIcon,
    ChartBarIcon,
    DevicePhoneMobileIcon
} from '@heroicons/react/24/outline';
import ThemeToggle from '../Themes/useTheme';

const Navigation = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const location = useLocation(); // Get current route

    const navigation = [
        { name: 'Dashboard', path: '/dashboard', icon: ChartBarIcon },
        { name: 'Networks', path: '/networks', icon: WifiIcon },
        { name: 'Discover', path: '/discover', icon: UserGroupIcon },
        { name: 'Admin', path: '/admin', icon: ShieldCheckIcon },
        { name: 'Captive', path: '/captive', icon: LockClosedIcon },
        { name: 'Devices', path: '/devices', icon: DevicePhoneMobileIcon },
        { name: 'Settings', path: '/settings', icon: CogIcon },
    ];

    const isActive = (path) => {
        if (path?.trim()) return location.pathname === path;

        return 'captive'
    };

    return (
        <>
            {/* Top Navigation Bar */}
            <nav className="sticky top-0 left-0 w-full z-30 relative bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <div className="mx-auto max-w-7xl px-2 sm:px-4 lg:px-6">
                    <div className="flex justify-between h-16">
                        {/* Logo and main nav */}
                        <div className="flex">
                            <div className="flex-shrink-0 flex items-center">
                                <div className="logo-icon text-xl">🌐</div>
                                <span className="ml-2 text-xl font-orbitron font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-[#00f0ff] dark:to-[#7b42f6] bg-clip-text text-transparent">
                                    NET-HUB
                                </span>
                            </div>

                            {/* Desktop Navigation */}
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-1">
                                {navigation.map((item) => (
                                    <a
                                        key={item.name}
                                        href={item.path}
                                        className={`${isActive(item.path)
                                            ? 'bg-blue-50 dark:bg-[#00f0ff]/10 text-blue-700 dark:text-[#00f0ff] border-blue-500 dark:border-[#00f0ff]'
                                            : 'text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-700 dark:hover:text-white border-transparent'
                                            } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium transition-all duration-200 cursor-pointer select-none`}
                                        onClick={() => { }}
                                    >
                                        <item.icon className="w-4 h-4 mr-2" />
                                        {item.name}
                                    </a>
                                ))}
                            </div>
                        </div>

                        {/* User menu and mobile button */}
                        <div className="hidden lg:flex items-center">
                            {/* Network Status */}
                            <div className="hidden md:flex items-center mr-4 px-3 py-1 rounded-full bg-green-50 dark:bg-[#00ff87]/10 border border-green-200 dark:border-[#00ff87]/30">
                                <div className="w-2 h-2 rounded-full bg-green-500 dark:bg-[#00ff87] mr-2 animate-pulse"></div>
                                <span className="text-xs font-medium text-green-700 dark:text-[#00ff87]">ONLINE</span>
                            </div>

                            {/* User Profile */}
                            <div className="hidden md:flex items-center space-x-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                                    S
                                </div>
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Skye</span>
                            </div>

                            {/* Theme Toggle */}
                            <div className="hidden md:flex items-center space-x-3 ml-2">
                                <ThemeToggle />
                            </div>

                            {/* Mobile menu button */}
                            <div className="sm:hidden">
                                <button
                                    type="button"
                                    className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
                                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                >
                                    {mobileMenuOpen ? (
                                        <XMarkIcon className="block h-6 w-6" />
                                    ) : (
                                        <Bars3Icon className="block h-6 w-6" />
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Mobile menu */}
                {mobileMenuOpen && (
                    <div
                        onMouseLeave={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="w-fit md:w-full border-x border-b border-r-none shadow-xl sm:border-none p-2 sm:p-0  sm:hidden absolute right-0 z-40 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                        <div className="pt-2 pb-3 space-y-1">
                            {navigation.map((item) => (
                                <a
                                    key={item.name}
                                    href={item.path}
                                    className={`${isActive(item.path)
                                        ? 'bg-blue-50 dark:bg-[#00f0ff]/10 text-blue-700 dark:text-[#00f0ff] border-l-4 border-blue-500 dark:border-[#00f0ff]'
                                        : 'text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-700 dark:hover:text-white border-l-4 border-transparent'
                                        } flex items-center px-4 py-3 text-base font-medium transition-all duration-200`}
                                    onClick={() => setMobileMenuOpen(false)}
                                >
                                    <item.icon className="w-5 h-5 mr-3" />
                                    {item.name}
                                </a>
                            ))}

                            {/*Theme toggle*/}
                            <div className='flex items-center gap-1 ml-4'>
                                <ThemeToggle /> <span className='text-gray-500 dark:text-gray-300 ml-2'>Change Theme</span>
                            </div>

                            {/* Mobile user info */}
                            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
                                <div className="flex items-center">
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold mr-3">
                                        S
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-gray-700 dark:text-gray-200">Skye</div>
                                        <div className="flex items-center mt-1">
                                            <div className="w-2 h-2 rounded-full bg-green-500 mr-1"></div>
                                            <span className="text-xs text-gray-500 dark:text-gray-400">Online</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </nav>

            {/* Quick Stats Bar */}
            <div className="hidden xs:flex bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex overflow-x-auto py-2 space-x-6">
                        <div className="flex items-center space-x-2 whitespace-nowrap">
                            <WifiIcon className="w-4 h-4 text-green-500" />
                            <span className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300"><span className='hidden sm:flex'>Active Networks:</span> <span className='font-bold mt-0.5'>3</span></span>
                        </div>
                        <div className="flex items-center space-x-2 whitespace-nowrap">
                            <DevicePhoneMobileIcon className="w-4 h-4 text-blue-500" />
                            <span className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300"><span className='hidden sm:flex'>Connected Devices:</span> <span className='font-bold mt-0.5'>12</span></span>
                        </div>
                        <div className="flex items-center space-x-2 whitespace-nowrap">
                            <UserGroupIcon className="w-4 h-4 text-purple-500" />
                            <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300"><span className='hidden sm:flex'>Online Users:</span> <span className='font-bold mt-0.5'>8</span></div>
                        </div>
                        <div className="hidden md:flex items-center space-x-2 whitespace-nowrap">
                            <ShieldCheckIcon className="w-4 h-4 text-green-500" />
                            <span className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300"><span className='hidden sm:flex'>Security:</span> <span className='font-bold mt-0.5'>Protected</span></span>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Navigation;
