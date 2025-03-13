document.addEventListener('DOMContentLoaded', function() {
    const totalVolumeInput = document.getElementById('total_volume');
    const netVolumeInput = document.getElementById('net_volume');
    const remainingBalanceInput = document.getElementById('remaining_balance');

    function calculateVolumes() {
        const totalVolume = parseFloat(totalVolumeInput.value) || 0;
        const netVolume = totalVolume * 0.70;
        const remainingBalance = totalVolume - netVolume;

        // Format to 2 decimal places
        netVolumeInput.value = netVolume.toFixed(2);
        remainingBalanceInput.value = remainingBalance.toFixed(2);
    }

    // Calculate on input change
    totalVolumeInput.addEventListener('input', calculateVolumes);
    
    // Initial calculation if there's a value
    calculateVolumes();
}); 