package testapp;

import java.util.ArrayList;

public class Block extends HashableObject{
    public String previous_hash;
    public ArrayList<Transaction> transactions;

    public Block(String p, ArrayList<Transaction> t){
        previous_hash = p;
        transactions = t;
    }

    public String getHash(){
        return Helper.getSHA256Hash(this.toJson());
    }
}