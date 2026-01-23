import { XMarkIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";


export const CreateNetworkModal = ({ newNetwork, setNewNetwork, handleCreateNetwork, loading, passwordVisible, setPasswordVisible }) => (
    <dialog id="create_network_modal" className="modal rounded-xl">
        <div className="modal-box bg-white dark:bg-primary-800 border border-gray-200 dark:border-gray-700 max-w-xl select-none p-4 rounded-xl">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Create New Network</h3>
                <button onClick={() => document.getElementById('create_network_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleCreateNetwork} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Network Name</label>
                        <input
                            type="text"
                            required
                            value={newNetwork.name}
                            onChange={(e) => setNewNetwork({ ...newNetwork, name: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                            placeholder="Office WiFi"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">SSID</label>
                        <input
                            type="text"
                            required
                            value={newNetwork.ssid}
                            onChange={(e) => setNewNetwork({ ...newNetwork, ssid: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                            placeholder="OfficeNet"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Security Type</label>
                        <select
                            value={newNetwork.security}
                            onChange={(e) => setNewNetwork({ ...newNetwork, security: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white">
                            <option value="wpa2">WPA2 Personal</option>
                            <option value="wpa3">WPA3 Personal</option>
                            <option value="enterprise">WPA2 Enterprise</option>
                            <option value="open">Open Network</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Band</label>
                        <select
                            value={newNetwork.band}
                            onChange={(e) => setNewNetwork({ ...newNetwork, band: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white">
                            <option value="2.4GHz">2.4GHz</option>
                            <option value="5GHz">5GHz</option>
                            <option value="2.4GHz & 5GHz">Dual Band</option>
                        </select>
                    </div>
                </div>

                {newNetwork.security !== 'open' && (
                    <div className='relative'>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Password</label>
                        <input
                            type={`${passwordVisible ? 'text' : 'password'}`}
                            required
                            value={newNetwork.password}
                            onChange={(e) => setNewNetwork({ ...newNetwork, password: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                            placeholder="Network password"
                        />
                        <EyeIcon
                            onClick={() => setPasswordVisible(true)}
                            className={`${passwordVisible ? 'hidden' : 'block'} absolute h-4 w-4 right-2 top-10 text-gray-800 dark:stroke-gray-100 cursor-pointer`} />
                        <EyeSlashIcon
                            onClick={() => setPasswordVisible(false)}
                            className={`${passwordVisible ? 'block' : 'hidden'} absolute h-4 w-4 right-2 top-10 text-gray-800 dark:stroke-gray-100 cursor-pointer`} />
                    </div>
                )}

                <div className="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        onClick={() => document.getElementById('create_network_modal').close()}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-primary-700 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Creating...' : 'Create Network'}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
);
