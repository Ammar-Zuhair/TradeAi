/**
 * Format Trade Type (1/2 -> Buy/Sell)
 */
export const getTradeTypeLabel = (type: number): 'BUY' | 'SELL' => {
    // Assumption: 1 = BUY, 2 = SELL (Common in MT4/5 bridges, but could be 0/1)
    // Adjusting based on standard conventions if not specified. 
    // User said: "1 to buy or 2 to sell" explicitly in prompt.
    return type === 1 ? 'BUY' : 'SELL';
};

/**
 * Format Trade Status
 */
export const getTradeStatusLabel = (status: number): 'OPEN' | 'CLOSED' | 'WIN' | 'LOSS' => {
    // Prompt doesn't explicitly map all status codes, but context implies:
    // 1 = Open (from AccountsContext logic)
    // User said "winning/losing" for status.
    switch (status) {
        case 1: return 'OPEN';
        case 2: return 'WIN';
        case 3: return 'LOSS';
        default: return 'CLOSED';
    }
};

/**
 * Format Account Type
 */
export const getAccountTypeLabel = (type: number): 'Demo' | 'Real' => {
    // Assumption: 0 = Demo, 1 = Real or similar. 
    // Context: "AccountType INT (Demo / Real)"
    // Let's assume 1=Real, 0=Demo for now, or string mapping if it comes as string?
    // User prompt said "INT".
    return type === 1 ? 'Real' : 'Demo';
};

/**
 * Format Transaction/Subscription Status
 * Status: (Completed / Pending / Failed)
 */
export const getTransactionStatusLabel = (status: number): string => {
    switch (status) {
        case 1: return 'Completed';
        case 0: return 'Pending';
        case -1: return 'Failed';
        default: return 'Unknown';
    }
};

/**
 * Format User Status (Boolean)
 */
export const getUserStatusLabel = (isActive: boolean): string => {
    return isActive ? 'Active' : 'Inactive';
};

/**
 * Generic Boolean Formatter
 */
export const formatBoolean = (value: boolean, trueText: string = 'Yes', falseText: string = 'No'): string => {
    return value ? trueText : falseText;
};
