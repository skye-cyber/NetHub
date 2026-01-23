import { XMarkIcon } from "@heroicons/react/24/outline";


export const CreateAccessCodeModal = ({ newAccessCode, setNewAccessCode, handleGenerateAccessCode, loading, networks }) => (
    <dialog id="create_code_modal" className="modal rounded-xl">
        <div className="modal-box bg-white dark:bg-primary-800 border border-gray-200 dark:border-gray-700 max-w-xl rounded-xl p-4 select-none">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Generate Access Code</h3>
                <button onClick={() => document.getElementById('create_code_modal').close()} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                    <XMarkIcon className="w-6 h-6" />
                </button>
            </div>
            <form onSubmit={handleGenerateAccessCode} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Network</label>
                    <select
                        required
                        value={newAccessCode.network}
                        onChange={(e) => setNewAccessCode({ ...newAccessCode, network: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white"
                    >
                        <option value="">Select a network</option>
                        {networks.map(network => (
                            <option key={network.id} value={network.name}>{network.name}</option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Maximum Uses</label>
                        <input
                            type="number"
                            required
                            min="1"
                            value={newAccessCode.maxUses}
                            onChange={(e) => setNewAccessCode({ ...newAccessCode, maxUses: parseInt(e.target.value) })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Expiration Date</label>
                        <input
                            type="date"
                            required
                            value={newAccessCode.expires}
                            onChange={(e) => setNewAccessCode({ ...newAccessCode, expires: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description (Optional)</label>
                    <input
                        type="text"
                        value={newAccessCode.description}
                        onChange={(e) => setNewAccessCode({ ...newAccessCode, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600  rounded-lg bg-white dark:bg-primary-700 text-gray-900 dark:text-white dark:placeholder-secondary-50 outline-none focus:ring dark:focus:ring-primary-100 focus:ring-none selection:bg-emerald-400/50 dark:selection:bg-emerald-600"
                        placeholder="e.g., Guest access for conference"
                    />
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        onClick={() => document.getElementById('create_code_modal').close()}
                        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-primary-700 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Generating...' : 'Generate Code'}
                    </button>
                </div>
            </form>
        </div>
    </dialog>
);
