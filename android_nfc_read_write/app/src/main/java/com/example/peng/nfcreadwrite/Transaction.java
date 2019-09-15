package com.example.peng.nfcreadwrite;

import com.google.gson.*;

import java.util.Date;
import java.text.SimpleDateFormat;

public class Transaction extends HashableObject{
    public String sender;
    public String recipient;
    public double amount;
    public String timestamp;
    public String signature;

    public Transaction(String s, String r, double a){
        sender = s;
        recipient = r;
        amount = a;
        timestamp = new SimpleDateFormat("yyy-MM-dd'T'HH:mm:ss").format(new Date());
        signature = null;
    }

    public String getHash(){
        Transaction tmp = new Transaction(this.sender, this.recipient, this.amount);
        tmp.timestamp = this.timestamp;
        return Helper.getSHA256Hash(tmp.toJson());
    }

    public static Transaction fromJson(String j){
        return new Gson().fromJson(j, Transaction.class);
    }
}