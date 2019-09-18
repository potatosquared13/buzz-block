package com.example.peng.nfcreadwrite;

import com.google.gson.*;

import java.util.Date;
import java.text.SimpleDateFormat;

public class Transaction extends HashableObject{
    int type;
    public String sender;
    public String address;
    public double amount;
    public String timestamp;
    public String signature;

    public Transaction(int type, String s, String r, double a){
        sender = s;
        address = r;
        amount = a;
        timestamp = new SimpleDateFormat("yyy-MM-dd'T'HH:mm:ss").format(new Date());
        signature = null;
    }

    public String getHash(){
        Transaction tmp = new Transaction(this.type, this.sender, this.address, this.amount);
        tmp.timestamp = this.timestamp;
        return Helper.getSHA256Hash(tmp.toJson());
    }

    public static Transaction fromJson(String j){
        return new Gson().fromJson(j, Transaction.class);
    }
}