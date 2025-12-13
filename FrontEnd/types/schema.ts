export interface DBUser {
    UserID: number;
    // Backend API returns 'UserIDcardrName' (with 'r'). User Spec asked for 'UserIDcardName'.
    UserIDCardName: string;
    // Backend Model uses 'UserIDCardNumber'. User Spec asked for 'UserIDCardrNumber'.
    UserIDCardNumber: number;
    Email: string;
    Password?: string;
    UserStatus: boolean;
    DateOfBirth: string; // ISO Date string
    Address: string;
    PhoneNumber: string;
    PushToken: string;
    IsNotificationsEnabled: boolean;
}

export interface DBAccount {
    AccountID: number;
    AccountName: string;
    UserID: number;
    AccountType: number; // 0=Demo, 1=Real
    AccountBalance: string; // DECIMAL
    AccountCreationDate: string;
    AccountLoginNumber: number;
    AccountLoginPassword?: string;
    ServerID: number;
    ServerName?: string; // ✅ Added for display
    RiskPercentage: string; // DECIMAL
    TradingStrategy: string;
}

export interface DBPlatform {
    BrokerID: number;
    BrokerName: string;
}

export interface DBPlatformServer {
    ServerID: number;
    BrokerID: number;
    ServerName: string;
}

export interface DBSubscription {
    TransactionID: number;
    AccountID: number;
    TransactionType: number;
    TransactionAmount: string; // DECIMAL
    TransactionDate: string;
    TransactionEnd: string;
    TransactionStatus: number;
}

export interface DBAssetType {
    AssetTypeID: number;
    TypeName: string;
}

export interface DBTradingPair {
    PairID: number;
    AssetTypeID: number;
    PairNameForSearch: string;
}

export interface DBAccountSymbolMapping {
    MappingID: number;
    AccountID: number;
    PairID: number;
    AccountSymbol: string;
}

export interface DBTrade {
    TradeID: number;
    AccountID: number;
    TradeType: number; // 1=Buy, 2=Sell (Assumption)
    MappingID: number;
    TradeLotsize: string; // DECIMAL
    TradeOpenPrice: string; // DECIMAL
    TradeClosePrice: string; // DECIMAL
    TradeOpenTime: string;
    TradeCloseTime: string;
    TradeSL: string; // DECIMAL
    TradeTP: string; // DECIMAL
    TradeProfitLose: string; // DECIMAL
    TradeStatus: number; // 1=Open, 2=Win, 3=Loss ??
    TradeAsset?: string; // Often joined in views
    AccountSymbol?: string; // ✅ Added
    PairName?: string;      // ✅ Added
}

export interface DBMarketAnalysisConfig {
    ConfigID: number;
    OurPairName: string;
    AccountID: number;
    IsActive: boolean;
    Timeframe: string;
    StrategyName: string;
}
